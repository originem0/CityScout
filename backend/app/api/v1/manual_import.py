"""Manual import API endpoints."""
import csv
import io
import json
import logging
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy import select

from app.api.deps import DbSession
from app.models import City, DataSource, Keyword, Job, Rent, ForumPost
from app.schemas.manual_import import (
    ImportDataType,
    ImportRequest,
    ImportPreviewResponse,
    ImportResultResponse,
    JobImportRow,
    RentImportRow,
    ForumImportRow,
    PlatformSearchGuide,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/import", tags=["import"])


# Platform configurations for search guide
PLATFORMS = {
    "boss": {
        "name": "Boss直聘",
        "base_url": "https://www.zhipin.com/web/geek/job",
        "search_pattern": "?query={keyword}&city={city_code}",
        "city_codes": {
            "深圳": "101280600",
            "广州": "101280100",
            "杭州": "101210100",
            "成都": "101270100",
            "武汉": "101200100",
            "南京": "101190100",
            "长沙": "101250100",
            "苏州": "101190400",
            "厦门": "101230200",
            "福州": "101230100",
        },
        "tips": [
            "Boss直聘反爬严格，建议手动搜索复制",
            "可以筛选薪资范围、经验要求等",
            "复制职位列表时，选中多行一起复制",
        ],
    },
    "zhihu": {
        "name": "知乎",
        "base_url": "https://www.zhihu.com/search",
        "search_pattern": "?type=content&q={keyword}",
        "tips": [
            "搜索「城市名 + 工作/生活/定居」等关键词",
            "优先查看高赞回答",
            "注意筛选近期回答（1年内）",
        ],
    },
    "weibo": {
        "name": "微博",
        "base_url": "https://s.weibo.com/weibo",
        "search_pattern": "?q={keyword}",
        "tips": [
            "可以搜索超话，如「#深圳生活#」",
            "筛选原创微博可以减少转发内容",
            "注意查看评论区的真实反馈",
        ],
    },
    "xiaohongshu": {
        "name": "小红书",
        "base_url": "https://www.xiaohongshu.com/search_result",
        "search_pattern": "?keyword={keyword}",
        "tips": [
            "小红书需要登录才能搜索",
            "搜索「城市名 + 打工/租房/生活成本」",
            "注意区分广告和真实分享",
        ],
    },
}


@router.get("/guide")
async def get_search_guide(
    db: DbSession,
    city_ids: str | None = None,
    keyword_category: str = "forum_topic",
) -> list[PlatformSearchGuide]:
    """Generate search guide for manual data collection."""
    # Get cities
    if city_ids:
        city_id_list = [int(x) for x in city_ids.split(",")]
        result = await db.execute(
            select(City).where(City.id.in_(city_id_list), City.enabled == True)
        )
    else:
        result = await db.execute(select(City).where(City.enabled == True))
    cities = result.scalars().all()

    # Get keywords
    result = await db.execute(
        select(Keyword).where(
            Keyword.category == keyword_category,
            Keyword.enabled == True,
        )
    )
    keywords = result.scalars().all()

    guides = []

    for platform_id, platform in PLATFORMS.items():
        search_urls = []

        for city in cities[:5]:  # Limit to 5 cities
            city_name = city.name

            # For Boss, use city code if available
            if platform_id == "boss":
                city_code = platform.get("city_codes", {}).get(city_name)
                if not city_code:
                    continue

                for keyword in keywords[:3]:  # Limit to 3 keywords
                    url = f"{platform['base_url']}{platform['search_pattern']}"
                    url = url.format(keyword=keyword.keyword, city_code=city_code)
                    search_urls.append({
                        "city": city_name,
                        "keyword": keyword.keyword,
                        "url": url,
                    })
            else:
                # For other platforms, use keyword with city name
                for keyword in keywords[:3]:
                    import urllib.parse
                    search_term = f"{city_name} {keyword.keyword}"
                    encoded_term = urllib.parse.quote(search_term)
                    url = f"{platform['base_url']}{platform['search_pattern']}"
                    url = url.format(keyword=encoded_term)
                    search_urls.append({
                        "city": city_name,
                        "keyword": keyword.keyword,
                        "url": url,
                    })

        guides.append(PlatformSearchGuide(
            platform=platform_id,
            platform_name=platform["name"],
            description=f"在{platform['name']}搜索城市相关内容",
            search_urls=search_urls,
            tips=platform["tips"],
        ))

    return guides


@router.get("/template/{data_type}")
async def download_template(data_type: ImportDataType):
    """Download CSV template for import."""
    if data_type == ImportDataType.job:
        headers = [
            "title", "company", "district", "salary_min", "salary_max",
            "salary_raw", "experience", "education", "tags", "description",
            "source_url", "posted_at"
        ]
        example = [
            "Python开发工程师", "某科技公司", "南山区", "15000", "25000",
            "15-25K", "3-5年", "本科", "五险一金,年终奖", "负责后端开发...",
            "https://example.com/job/123", "2024-01-15"
        ]
    elif data_type == ImportDataType.rent:
        headers = [
            "title", "property_type", "district", "neighborhood", "price",
            "price_raw", "area", "layout", "floor", "subway_info",
            "facilities", "source_url", "posted_at"
        ]
        example = [
            "精装两房近地铁", "整租", "福田区", "XX花园", "3500",
            "3500元/月", "65", "2室1厅", "中层/18层", "1号线 车公庙站",
            "空调,洗衣机,冰箱", "https://example.com/rent/456", "2024-01-15"
        ]
    else:  # forum
        headers = [
            "title", "content", "author", "topic", "likes",
            "replies_count", "source_url", "posted_at"
        ]
        example = [
            "深圳工作三年的感受", "在深圳工作三年了，说说我的真实感受...",
            "匿名用户", "深圳", "128", "45",
            "https://example.com/post/789", "2024-01-15"
        ]

    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerow(example)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={data_type.value}_template.csv"
        },
    )


@router.post("/preview")
async def preview_import(
    db: DbSession,
    file: UploadFile = File(...),
    data_type: str = Form(...),
    city_id: int = Form(...),
    data_source_id: int = Form(...),
) -> ImportPreviewResponse:
    """Preview import data before committing."""
    # Validate city and data source
    city = await db.get(City, city_id)
    if not city:
        raise HTTPException(status_code=400, detail="City not found")

    data_source = await db.get(DataSource, data_source_id)
    if not data_source:
        raise HTTPException(status_code=400, detail="Data source not found")

    # Parse file
    content = await file.read()
    try:
        rows = _parse_file(content, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    # Validate rows
    valid_rows = []
    errors = []

    row_class = _get_row_class(ImportDataType(data_type))

    for i, row in enumerate(rows):
        try:
            validated = row_class(**row)
            valid_rows.append(validated.model_dump())
        except ValidationError as e:
            for error in e.errors():
                errors.append({
                    "row": i + 1,
                    "field": error["loc"][0] if error["loc"] else "unknown",
                    "error": error["msg"],
                })

    return ImportPreviewResponse(
        total_rows=len(rows),
        valid_rows=len(valid_rows),
        invalid_rows=len(rows) - len(valid_rows),
        errors=errors[:20],  # Limit to first 20 errors
        preview=valid_rows[:10],  # Preview first 10 rows
    )


@router.post("/execute")
async def execute_import(
    db: DbSession,
    file: UploadFile = File(...),
    data_type: str = Form(...),
    city_id: int = Form(...),
    data_source_id: int = Form(...),
) -> ImportResultResponse:
    """Execute the import."""
    # Validate city and data source
    city = await db.get(City, city_id)
    if not city:
        raise HTTPException(status_code=400, detail="City not found")

    data_source = await db.get(DataSource, data_source_id)
    if not data_source:
        raise HTTPException(status_code=400, detail="Data source not found")

    # Parse file
    content = await file.read()
    try:
        rows = _parse_file(content, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    # Import rows
    data_type_enum = ImportDataType(data_type)
    row_class = _get_row_class(data_type_enum)

    imported_count = 0
    skipped_count = 0
    errors = []

    for i, row in enumerate(rows):
        try:
            validated = row_class(**row)
            await _save_row(db, data_type_enum, validated, city_id, data_source_id)
            imported_count += 1
        except ValidationError as e:
            skipped_count += 1
            errors.append({
                "row": i + 1,
                "error": str(e.errors()[0]["msg"]) if e.errors() else "Validation error",
            })
        except Exception as e:
            skipped_count += 1
            errors.append({
                "row": i + 1,
                "error": str(e),
            })

    await db.commit()

    return ImportResultResponse(
        success=imported_count > 0,
        imported_count=imported_count,
        skipped_count=skipped_count,
        errors=errors[:20],
    )


@router.post("/json")
async def import_json(
    db: DbSession,
    request: ImportRequest,
) -> ImportResultResponse:
    """Import data from JSON."""
    # Validate city and data source
    city = await db.get(City, request.city_id)
    if not city:
        raise HTTPException(status_code=400, detail="City not found")

    data_source = await db.get(DataSource, request.data_source_id)
    if not data_source:
        raise HTTPException(status_code=400, detail="Data source not found")

    row_class = _get_row_class(request.data_type)

    imported_count = 0
    skipped_count = 0
    errors = []

    for i, row in enumerate(request.rows):
        try:
            validated = row_class(**row)
            await _save_row(db, request.data_type, validated, request.city_id, request.data_source_id)
            imported_count += 1
        except ValidationError as e:
            skipped_count += 1
            errors.append({
                "row": i + 1,
                "error": str(e.errors()[0]["msg"]) if e.errors() else "Validation error",
            })
        except Exception as e:
            skipped_count += 1
            errors.append({
                "row": i + 1,
                "error": str(e),
            })

    await db.commit()

    return ImportResultResponse(
        success=imported_count > 0,
        imported_count=imported_count,
        skipped_count=skipped_count,
        errors=errors[:20],
    )


def _parse_file(content: bytes, filename: str) -> list[dict]:
    """Parse CSV or Excel file into list of dicts."""
    if filename.endswith(".csv"):
        return _parse_csv(content)
    elif filename.endswith((".xlsx", ".xls")):
        return _parse_excel(content)
    else:
        raise ValueError("Unsupported file format. Use CSV or Excel.")


def _parse_csv(content: bytes) -> list[dict]:
    """Parse CSV content."""
    # Try different encodings
    for encoding in ["utf-8", "utf-8-sig", "gbk", "gb2312"]:
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Failed to decode CSV file")

    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        # Clean up empty values
        cleaned = {k: v.strip() if v else None for k, v in row.items()}
        rows.append(cleaned)
    return rows


def _parse_excel(content: bytes) -> list[dict]:
    """Parse Excel content."""
    import openpyxl

    workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
    sheet = workbook.active

    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return []

    headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(rows[0])]

    result = []
    for row in rows[1:]:
        if not any(row):  # Skip empty rows
            continue
        row_dict = {}
        for i, value in enumerate(row):
            if i < len(headers):
                row_dict[headers[i]] = str(value).strip() if value else None
        result.append(row_dict)

    return result


def _get_row_class(data_type: ImportDataType):
    """Get the appropriate row class for validation."""
    if data_type == ImportDataType.job:
        return JobImportRow
    elif data_type == ImportDataType.rent:
        return RentImportRow
    else:
        return ForumImportRow


async def _save_row(
    db: DbSession,
    data_type: ImportDataType,
    row: JobImportRow | RentImportRow | ForumImportRow,
    city_id: int,
    data_source_id: int,
):
    """Save a validated row to the database."""
    source_id = f"manual_{uuid.uuid4().hex[:12]}"

    if data_type == ImportDataType.job:
        obj = Job(
            data_source_id=data_source_id,
            city_id=city_id,
            source_id=source_id,
            source_url=row.source_url,
            title=row.title,
            company=row.company,
            district=row.district,
            salary_min=row.salary_min,
            salary_max=row.salary_max,
            salary_raw=row.salary_raw,
            experience=row.experience,
            education=row.education,
            tags=row.tags,
            description=row.description,
            posted_at=row.posted_at,
        )
    elif data_type == ImportDataType.rent:
        obj = Rent(
            data_source_id=data_source_id,
            city_id=city_id,
            source_id=source_id,
            source_url=row.source_url,
            title=row.title,
            property_type=row.property_type,
            district=row.district,
            neighborhood=row.neighborhood,
            price=row.price,
            price_raw=row.price_raw,
            area=row.area,
            layout=row.layout,
            floor=row.floor,
            subway_info=row.subway_info,
            facilities=row.facilities,
            posted_at=row.posted_at,
        )
    else:  # forum
        obj = ForumPost(
            data_source_id=data_source_id,
            city_id=city_id,
            source_id=source_id,
            source_url=row.source_url,
            post_type="post",
            title=row.title,
            content=row.content,
            author=row.author,
            topic=row.topic,
            likes=row.likes,
            replies_count=row.replies_count,
            posted_at=row.posted_at,
        )

    db.add(obj)
