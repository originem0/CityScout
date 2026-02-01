"""58同城招聘爬虫实现."""
import hashlib
import logging
import os
import re
from datetime import datetime
from decimal import Decimal
from typing import Callable, Awaitable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.crawlers.base import BaseCrawler
from app.crawlers.constants import CITY_CODES_58
from app.models import Job, City, DataSource, Keyword

logger = logging.getLogger(__name__)

# 预编译薪资解析正则表达式
_SALARY_RANGE = re.compile(
    r"(\d+(?:\.\d+)?)\s*[-~到至]\s*(\d+(?:\.\d+)?)\s*(千|K|k|万|元)?",
)
_SALARY_ABOVE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(千|K|k|万|元)?\s*以上",
)
_SALARY_SINGLE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(千|K|k|万|元)?",
)
_SALARY_NEGOTIABLE = re.compile(r"面议|待遇面议|薪资面议")
_SALARY_ANNUAL = re.compile(
    r"(\d+(?:\.\d+)?)\s*[-~到至]\s*(\d+(?:\.\d+)?)\s*万?\s*/?\s*年",
)

# 经验和学历正则
_EXP_PATTERN = re.compile(r"(\d+[-~]\d+年|\d+年以上|应届|不限|经验不限)")
_EDU_PATTERN = re.compile(r"(本科|大专|硕士|博士|高中|中专|学历不限)")


class JobCrawler(BaseCrawler):
    """58同城招聘页面爬虫."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.db_session_factory = None
        self.exclude_keywords = []

    async def _init_db(self):
        """Initialize database connection."""
        engine = create_async_engine(settings.DATABASE_URL)
        self.db_session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

    async def _get_city_info(self, db: AsyncSession) -> tuple[str, str] | None:
        """Get city name and 58.com code."""
        if not self.city_id:
            return None

        result = await db.execute(select(City).where(City.id == self.city_id))
        city = result.scalar_one_or_none()
        if not city:
            return None

        city_code = CITY_CODES_58.get(city.name)
        if not city_code:
            logger.warning(f"No 58.com city code mapping for: {city.name}")
            return None

        return city.name, city_code

    async def _get_search_keyword(self, db: AsyncSession) -> str | None:
        """Get search keyword if specified."""
        if not self.keyword_id:
            return None

        result = await db.execute(select(Keyword).where(Keyword.id == self.keyword_id))
        keyword = result.scalar_one_or_none()
        return keyword.keyword if keyword else None

    async def _load_exclude_keywords(self, db: AsyncSession):
        """Load exclude keywords for filtering."""
        result = await db.execute(
            select(Keyword).where(
                Keyword.category == "job_exclude",
                Keyword.enabled == True,
            )
        )
        keywords = result.scalars().all()
        self.exclude_keywords = [k.keyword.lower() for k in keywords]
        logger.info(f"Loaded {len(self.exclude_keywords)} exclude keywords")

    def _should_exclude(self, title: str, company: str = "") -> bool:
        """Check if job should be excluded based on keywords."""
        text = f"{title} {company}".lower()
        for kw in self.exclude_keywords:
            if kw in text:
                return True
        return False

    def _parse_salary(self, salary_text: str) -> tuple[Decimal | None, Decimal | None]:
        """Parse salary text into min/max values (元/月).

        Handles formats:
          - "8000-15000元/月"
          - "8-15K", "8-15千"
          - "2-3万"
          - "15K以上"
          - "20-40万/年" (converts to monthly)
          - "面议" (returns None, None)
        """
        if not salary_text:
            return None, None

        # Clean the text
        salary_text = salary_text.replace(",", "").replace(" ", "").replace("，", "")

        # 面议 / 薪资面议
        if _SALARY_NEGOTIABLE.search(salary_text):
            return None, None

        # 年薪范围 "20-40万/年" → 转月薪
        match = _SALARY_ANNUAL.search(salary_text)
        if match:
            min_val = float(match.group(1)) * 10000 / 12
            max_val = float(match.group(2)) * 10000 / 12
            return Decimal(str(round(min_val, 2))), Decimal(str(round(max_val, 2)))

        # 薪资范围 "8000-15000元/月" or "8-15K"
        match = _SALARY_RANGE.search(salary_text)
        if match:
            min_val = float(match.group(1))
            max_val = float(match.group(2))
            unit = match.group(3) or ""

            if unit.lower() in ["千", "k"]:
                min_val *= 1000
                max_val *= 1000
            elif unit == "万":
                min_val *= 10000
                max_val *= 10000

            return Decimal(str(min_val)), Decimal(str(max_val))

        # "15K以上" 格式
        match = _SALARY_ABOVE.search(salary_text)
        if match:
            val = float(match.group(1))
            unit = match.group(2) or ""

            if unit.lower() in ["千", "k"]:
                val *= 1000
            elif unit == "万":
                val *= 10000

            return Decimal(str(val)), None  # 只有下限

        # 单一数值 "8000元/月"
        match = _SALARY_SINGLE.search(salary_text)
        if match:
            val = float(match.group(1))
            unit = match.group(2) or ""

            if unit.lower() in ["千", "k"]:
                val *= 1000
            elif unit == "万":
                val *= 10000

            return Decimal(str(val)), Decimal(str(val))

        return None, None

    async def crawl(
        self,
        on_progress: Callable[[int, int], Awaitable[None]] | None = None,
    ) -> dict:
        """Crawl 58同城 job listings with pagination support.

        Args:
            on_progress: Callback for progress updates (progress%, record_count)

        Returns:
            dict with crawl results including records_count
        """
        await self._init_db()

        # 从配置读取最大页数，默认5页
        max_pages = self.config.get("max_pages", 5)

        async with self.db_session_factory() as db:
            # Get city info
            city_info = await self._get_city_info(db)
            if not city_info:
                raise ValueError(f"City not found or not supported: {self.city_id}")

            city_name, city_code = city_info
            logger.info(f"Starting job crawl for {city_name} (code: {city_code}), max_pages={max_pages}")

            # Get search keyword if any
            search_keyword = await self._get_search_keyword(db)

            # Load exclude keywords
            await self._load_exclude_keywords(db)

            # Build URL
            base_url = f"https://{city_code}.58.com/job/"
            if search_keyword:
                # URL encode the keyword for search
                import urllib.parse
                encoded_keyword = urllib.parse.quote(search_keyword)
                url = f"{base_url}?key={encoded_keyword}"
            else:
                url = base_url

            logger.info(f"Crawling URL: {url}")

            # Navigate to first page
            success = await self.goto_with_retry(url)
            if not success:
                raise Exception(f"Failed to load page: {url}")

            # Wait for job listings to load
            await self.wait_for_selector_safe(".job_list li", timeout=15000)

            # Try to detect total pages
            total_pages = await self.get_total_pages()
            if total_pages:
                # Limit to max_pages
                total_pages = min(total_pages, max_pages)
                logger.info(f"Detected {total_pages} pages (limited to {max_pages})")
            else:
                total_pages = max_pages
                logger.info(f"Could not detect total pages, using max_pages={max_pages}")

            all_jobs_data = []
            current_page = 1

            while current_page <= total_pages:
                logger.info(f"Parsing page {current_page}/{total_pages}")

                # Scroll to load more content
                await self.scroll_page(scroll_count=3)

                # Parse job listings from current page
                page_jobs = await self._parse_job_list()
                all_jobs_data.extend(page_jobs)

                # Report progress
                if on_progress:
                    progress_pct = int((current_page / total_pages) * 80)  # Reserve 20% for saving
                    await on_progress(progress_pct, len(all_jobs_data))

                # Check if we should continue to next page
                if current_page >= total_pages:
                    break

                # 58同城分页 selectors
                next_selectors = [
                    "a.next",
                    ".pager a.next",
                    "a[class*='next']",
                    "a:has-text('下一页')",
                ]

                # Try to navigate to next page
                has_next = await self.click_next_page(next_selectors)
                if not has_next:
                    logger.info(f"No more pages after page {current_page}")
                    break

                # Wait for new content to load
                await self.wait_for_selector_safe(".job_list li", timeout=15000)

                # Random delay between pages (3-5 seconds for anti-detection)
                await self.wait_random(3.0, 5.0)
                current_page += 1

            logger.info(f"Total jobs collected from {current_page} pages: {len(all_jobs_data)}")

            # Filter excluded jobs
            filtered_jobs = [
                j for j in all_jobs_data
                if not self._should_exclude(j.get("title", ""), j.get("company", ""))
            ]
            logger.info(
                f"Filtered {len(all_jobs_data) - len(filtered_jobs)} jobs by exclude keywords"
            )

            if on_progress:
                await on_progress(90, len(filtered_jobs))

            # Save to database
            saved_count = await self._save_jobs(db, filtered_jobs, city_name)

            if on_progress:
                await on_progress(100, saved_count)

            return {
                "records_count": saved_count,
                "city": city_name,
                "total_found": len(all_jobs_data),
                "filtered_out": len(all_jobs_data) - len(filtered_jobs),
                "pages_crawled": current_page,
            }

    async def _parse_job_list(self) -> list[dict]:
        """Parse job listings from the current page."""
        jobs = []

        # Try different selectors for 58同城 job listings
        # 58同城 has multiple page layouts
        selectors = [
            ".job_list li",
            ".list-item",
            "[class*='job'] li",
        ]

        items = []
        for selector in selectors:
            items = await self.page.query_selector_all(selector)
            if items:
                logger.info(f"Found {len(items)} job items with selector: {selector}")
                break

        if not items:
            logger.warning("No job listings found on page")
            # Take a screenshot for debugging with unique path
            task_id = self.config.get("task_id", "unknown")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_dir = "logs/screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)
            await self.page.screenshot(path=f"{screenshot_dir}/job_{task_id}_{timestamp}.png")
            return jobs

        for item in items:
            try:
                job_data = await self._parse_job_item(item)
                if job_data:
                    jobs.append(job_data)
            except Exception as e:
                logger.warning(f"Failed to parse job item: {e}")
                continue

        logger.info(f"Parsed {len(jobs)} job listings")
        return jobs

    async def _parse_job_item(self, item) -> dict | None:
        """Parse a single job listing element."""
        try:
            # Extract job title and link
            title_el = await item.query_selector("a.job_title, .job-name a, a[href*='job']")
            if not title_el:
                return None

            title = await title_el.text_content()
            title = title.strip() if title else ""
            if not title:
                return None

            href = await title_el.get_attribute("href")
            source_url = href if href and href.startswith("http") else None

            # Extract source_id from URL
            source_id = ""
            if source_url:
                match = re.search(r"/(\d+)x?\.shtml", source_url)
                if match:
                    source_id = match.group(1)

            if not source_id:
                # 使用 hashlib.md5 生成稳定的 source_id（hash() 跨进程不稳定）
                source_id = f"58job_{hashlib.md5(title.encode()).hexdigest()[:16]}"

            # Extract company name
            company_el = await item.query_selector(".comp_name, .company-name, [class*='company']")
            company = ""
            if company_el:
                company = await company_el.text_content()
                company = company.strip() if company else ""

            # Extract salary
            salary_el = await item.query_selector(".job_salary, .salary, [class*='salary']")
            salary_raw = ""
            if salary_el:
                salary_raw = await salary_el.text_content()
                salary_raw = salary_raw.strip() if salary_raw else ""

            salary_min, salary_max = self._parse_salary(salary_raw)

            # Extract location/district
            area_el = await item.query_selector(".job_add, .area, [class*='area'], [class*='address']")
            district = ""
            if area_el:
                district = await area_el.text_content()
                district = district.strip() if district else ""

            # Extract experience and education
            welfare_el = await item.query_selector(".job_require, .require, [class*='welfare']")
            experience = ""
            education = ""
            if welfare_el:
                welfare_text = await welfare_el.text_content()
                welfare_text = welfare_text if welfare_text else ""

                # Parse experience like "3-5年"
                exp_match = _EXP_PATTERN.search(welfare_text)
                if exp_match:
                    experience = exp_match.group(1)

                # Parse education
                edu_match = _EDU_PATTERN.search(welfare_text)
                if edu_match:
                    education = edu_match.group(1)

            # Extract tags/benefits
            tags_el = await item.query_selector_all(".job_tag span, .tags span, [class*='tag'] span")
            tags = []
            for tag_el in tags_el[:5]:  # Limit to 5 tags
                tag_text = await tag_el.text_content()
                if tag_text:
                    tags.append(tag_text.strip())

            return {
                "source_id": source_id,
                "source_url": source_url,
                "title": title,
                "company": company,
                "salary_raw": salary_raw,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "district": district,
                "experience": experience,
                "education": education,
                "tags": ",".join(tags) if tags else None,
            }

        except Exception as e:
            logger.warning(f"Error parsing job item: {e}")
            return None

    async def _save_jobs(
        self, db: AsyncSession, jobs_data: list[dict], city_name: str
    ) -> int:
        """Save job listings to database with upsert (deduplication)."""
        saved_count = 0

        for job_data in jobs_data:
            try:
                values = {
                    "data_source_id": self.data_source_id,
                    "city_id": self.city_id,
                    "crawl_task_id": UUID(self.config.get("task_id")) if self.config.get("task_id") else None,
                    "source_id": job_data["source_id"],
                    "source_url": job_data.get("source_url"),
                    "title": job_data["title"],
                    "company": job_data.get("company"),
                    "district": job_data.get("district"),
                    "salary_min": job_data.get("salary_min"),
                    "salary_max": job_data.get("salary_max"),
                    "salary_raw": job_data.get("salary_raw"),
                    "experience": job_data.get("experience"),
                    "education": job_data.get("education"),
                    "tags": job_data.get("tags"),
                }

                # 使用 PostgreSQL upsert: 如果 source_id 已存在则更新
                stmt = insert(Job).values(**values)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["source_id"],
                    set_={
                        "title": stmt.excluded.title,
                        "company": stmt.excluded.company,
                        "district": stmt.excluded.district,
                        "salary_min": stmt.excluded.salary_min,
                        "salary_max": stmt.excluded.salary_max,
                        "salary_raw": stmt.excluded.salary_raw,
                        "experience": stmt.excluded.experience,
                        "education": stmt.excluded.education,
                        "tags": stmt.excluded.tags,
                        "crawl_task_id": stmt.excluded.crawl_task_id,
                    },
                )
                await db.execute(stmt)
                saved_count += 1

            except Exception as e:
                logger.warning(f"Failed to save job: {e}")
                continue

        await db.commit()
        logger.info(f"Saved/updated {saved_count} jobs to database")
        return saved_count
