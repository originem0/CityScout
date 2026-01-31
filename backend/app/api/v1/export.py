"""Data export API endpoints."""
import io
import csv
from datetime import datetime

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func

from app.api.deps import DbSession
from app.models import Job, Rent, ForumPost, City

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/excel/city-comparison")
async def export_city_comparison_excel(
    db: DbSession,
    city_ids: str | None = Query(None),
):
    """Export city comparison data as CSV (Excel-compatible)."""
    # Get cities
    if city_ids:
        cids = [int(x) for x in city_ids.split(",") if x.strip()]
        city_query = select(City).where(City.id.in_(cids))
    else:
        city_query = select(City).where(City.enabled == True)

    cities_result = await db.execute(city_query)
    cities = cities_result.scalars().all()
    city_id_list = [c.id for c in cities]

    # Job stats
    job_q = (
        select(
            Job.city_id,
            func.count(Job.id).label("job_count"),
            func.avg(Job.salary_min).label("avg_salary_min"),
            func.avg(Job.salary_max).label("avg_salary_max"),
        )
        .where(Job.city_id.in_(city_id_list))
        .group_by(Job.city_id)
    )
    job_result = await db.execute(job_q)
    job_data = {r.city_id: r for r in job_result.all()}

    # Rent stats
    rent_q = (
        select(
            Rent.city_id,
            func.count(Rent.id).label("rent_count"),
            func.avg(Rent.price).label("avg_rent"),
        )
        .where(Rent.city_id.in_(city_id_list))
        .group_by(Rent.city_id)
    )
    rent_result = await db.execute(rent_q)
    rent_data = {r.city_id: r for r in rent_result.all()}

    # Forum stats
    forum_q = (
        select(
            ForumPost.city_id,
            func.count(ForumPost.id).label("post_count"),
        )
        .where(ForumPost.city_id.in_(city_id_list))
        .group_by(ForumPost.city_id)
    )
    forum_result = await db.execute(forum_q)
    forum_data = {r.city_id: r.post_count for r in forum_result.all()}

    # Build CSV with BOM for Excel
    output = io.StringIO()
    output.write("\ufeff")  # BOM for Excel UTF-8
    writer = csv.writer(output)
    writer.writerow([
        "城市", "省份", "城市等级",
        "岗位数", "平均薪资下限", "平均薪资上限",
        "房源数", "平均租金",
        "薪租比",
        "论坛帖子数",
    ])

    for city in cities:
        js = job_data.get(city.id)
        rs = rent_data.get(city.id)
        fs = forum_data.get(city.id, 0)

        avg_salary_min = round(float(js.avg_salary_min), 0) if js and js.avg_salary_min else ""
        avg_salary_max = round(float(js.avg_salary_max), 0) if js and js.avg_salary_max else ""
        avg_rent = round(float(rs.avg_rent), 0) if rs and rs.avg_rent else ""

        ratio = ""
        if avg_salary_min and avg_salary_max and avg_rent:
            avg_sal = (float(avg_salary_min) + float(avg_salary_max)) / 2
            ratio = round(avg_sal / float(avg_rent), 1) if float(avg_rent) > 0 else ""

        writer.writerow([
            city.name, city.province, city.tier,
            js.job_count if js else 0, avg_salary_min, avg_salary_max,
            rs.rent_count if rs else 0, avg_rent,
            ratio,
            fs,
        ])

    output.seek(0)
    filename = f"city_comparison_{datetime.now().strftime('%Y%m%d')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/markdown/forum-summary")
async def export_forum_summary_markdown(
    db: DbSession,
    city_id: int | None = None,
    limit: int = Query(50, ge=1, le=200),
):
    """Export forum posts as Markdown summary."""
    query = (
        select(ForumPost)
        .order_by(ForumPost.likes.desc(), ForumPost.replies_count.desc())
        .limit(limit)
    )
    if city_id:
        query = query.where(ForumPost.city_id == city_id)

    result = await db.execute(query)
    posts = result.scalars().all()

    # Get city name
    city_name = "所有城市"
    if city_id:
        city_result = await db.execute(select(City).where(City.id == city_id))
        city = city_result.scalars().first()
        if city:
            city_name = city.name

    lines = [
        f"# {city_name} - 论坛评论汇总\n",
        f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        f"> 共 {len(posts)} 条帖子，按热度排序\n",
        "---\n",
    ]

    for i, post in enumerate(posts, 1):
        title = post.title or "无标题"
        lines.append(f"## {i}. {title}\n")
        lines.append(f"**作者**: {post.author or '匿名'} | "
                      f"**点赞**: {post.likes} | "
                      f"**回复**: {post.replies_count}")
        if post.posted_at:
            lines.append(f" | **时间**: {post.posted_at.strftime('%Y-%m-%d')}")
        lines.append("\n")

        content = post.content or ""
        if len(content) > 500:
            content = content[:500] + "..."
        lines.append(f"{content}\n")

        if post.source_url:
            lines.append(f"[原文链接]({post.source_url})\n")
        lines.append("---\n")

    md_content = "\n".join(lines)
    filename = f"forum_summary_{city_name}_{datetime.now().strftime('%Y%m%d')}.md"

    return StreamingResponse(
        iter([md_content]),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@router.get("/ai-report")
async def generate_ai_report_prompt(
    db: DbSession,
    city_ids: str | None = Query(None),
):
    """Generate a prompt for AI analysis (e.g., for Deep Research)."""
    # Gather data same as city-comparison
    if city_ids:
        cids = [int(x) for x in city_ids.split(",") if x.strip()]
        city_query = select(City).where(City.id.in_(cids))
    else:
        city_query = select(City).where(City.enabled == True)

    cities_result = await db.execute(city_query)
    cities = cities_result.scalars().all()
    city_id_list = [c.id for c in cities]

    # Job stats
    job_q = (
        select(
            Job.city_id,
            func.count(Job.id).label("cnt"),
            func.avg(Job.salary_min).label("avg_min"),
            func.avg(Job.salary_max).label("avg_max"),
        )
        .where(Job.city_id.in_(city_id_list))
        .group_by(Job.city_id)
    )
    job_result = await db.execute(job_q)
    job_data = {r.city_id: r for r in job_result.all()}

    # Rent stats
    rent_q = (
        select(
            Rent.city_id,
            func.count(Rent.id).label("cnt"),
            func.avg(Rent.price).label("avg_price"),
        )
        .where(Rent.city_id.in_(city_id_list))
        .group_by(Rent.city_id)
    )
    rent_result = await db.execute(rent_q)
    rent_data = {r.city_id: r for r in rent_result.all()}

    # Build data summary
    city_summaries = []
    for city in cities:
        js = job_data.get(city.id)
        rs = rent_data.get(city.id)
        summary = f"- **{city.name}**（{city.province}，{city.tier}）"
        if js:
            summary += f"：{js.cnt}个岗位，平均薪资 {round(float(js.avg_min)):,}-{round(float(js.avg_max)):,}元/月"
        if rs:
            summary += f"，{rs.cnt}个房源，平均租金 {round(float(rs.avg_price)):,}元/月"
        city_summaries.append(summary)

    prompt = f"""# 城市分析报告生成提示词

## 背景
我正在评估以下南方城市作为工作和生活的目标城市。以下是我采集的数据摘要。

## 数据摘要（截至 {datetime.now().strftime('%Y-%m-%d')}）

{chr(10).join(city_summaries)}

## 请帮我分析以下内容

1. **综合排名**：基于薪资水平、生活成本（租金）、薪租比，对这些城市进行综合排名
2. **性价比分析**：哪些城市的薪资相对生活成本最优？
3. **行业分析**：各城市的主要招聘行业和岗位特点
4. **生活质量**：结合气候、交通、文化等因素的综合评价
5. **建议**：对于一个IT从业者，你推荐哪3个城市？为什么？

## 输出格式
请以结构化的 Markdown 格式输出，包含数据表格和分析说明。
"""

    return {
        "prompt": prompt,
        "city_count": len(cities),
        "generated_at": datetime.now().isoformat(),
    }
