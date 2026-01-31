"""58同城招聘爬虫实现."""
import logging
import re
from datetime import datetime
from decimal import Decimal
from typing import Callable, Awaitable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.crawlers.base import BaseCrawler
from app.models import Job, City, DataSource, Keyword

logger = logging.getLogger(__name__)

# 58同城城市代码映射
CITY_CODES = {
    "深圳": "sz",
    "广州": "gz",
    "杭州": "hz",
    "成都": "cd",
    "武汉": "wh",
    "南京": "nj",
    "长沙": "cs",
    "苏州": "su",
    "厦门": "xm",
    "福州": "fz",
    "珠海": "zh",
    "东莞": "dg",
    "佛山": "fs",
    "昆明": "km",
    "南宁": "nn",
    "贵阳": "gy",
    "海口": "hk",
    "三亚": "sanya",
    "无锡": "wx",
    "宁波": "nb",
}


class JobCrawler(BaseCrawler):
    """58同城招聘页面爬虫."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.db_session_factory = None
        self.jobs_collected = []
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

        city_code = CITY_CODES.get(city.name)
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
        """Parse salary text like '8000-15000元/月' into min/max values."""
        if not salary_text:
            return None, None

        # Clean the text
        salary_text = salary_text.replace(",", "").replace(" ", "")

        # Pattern for range: "8000-15000元/月" or "8-15K"
        range_pattern = r"(\d+(?:\.\d+)?)\s*[-~到至]\s*(\d+(?:\.\d+)?)\s*(千|K|k|万|元)?"
        match = re.search(range_pattern, salary_text)

        if match:
            min_val = float(match.group(1))
            max_val = float(match.group(2))
            unit = match.group(3) or ""

            # Convert to yuan/month
            if unit.lower() in ["千", "k"]:
                min_val *= 1000
                max_val *= 1000
            elif unit == "万":
                min_val *= 10000
                max_val *= 10000

            return Decimal(str(min_val)), Decimal(str(max_val))

        # Pattern for single value: "面议" or "8000元/月"
        single_pattern = r"(\d+(?:\.\d+)?)\s*(千|K|k|万|元)?"
        match = re.search(single_pattern, salary_text)

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
        """Crawl 58同城 job listings.

        Args:
            on_progress: Callback for progress updates (progress%, record_count)

        Returns:
            dict with crawl results including records_count
        """
        await self._init_db()

        async with self.db_session_factory() as db:
            # Get city info
            city_info = await self._get_city_info(db)
            if not city_info:
                raise ValueError(f"City not found or not supported: {self.city_id}")

            city_name, city_code = city_info
            logger.info(f"Starting job crawl for {city_name} (code: {city_code})")

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

            # Navigate to page
            success = await self.goto_with_retry(url)
            if not success:
                raise Exception(f"Failed to load page: {url}")

            # Wait for job listings to load
            await self.wait_for_selector_safe(".job_list li", timeout=15000)

            # Scroll to load more content
            await self.scroll_page(scroll_count=3)

            # Parse job listings
            jobs_data = await self._parse_job_list()

            if on_progress:
                await on_progress(50, len(jobs_data))

            # Filter excluded jobs
            filtered_jobs = [
                j for j in jobs_data
                if not self._should_exclude(j.get("title", ""), j.get("company", ""))
            ]
            logger.info(
                f"Filtered {len(jobs_data) - len(filtered_jobs)} jobs by exclude keywords"
            )

            # Save to database
            saved_count = await self._save_jobs(db, filtered_jobs, city_name)

            if on_progress:
                await on_progress(100, saved_count)

            return {
                "records_count": saved_count,
                "city": city_name,
                "total_found": len(jobs_data),
                "filtered_out": len(jobs_data) - len(filtered_jobs),
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
            # Take a screenshot for debugging
            await self.page.screenshot(path="debug_job_page.png")
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
                source_id = f"58_{hash(title)}"

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
                exp_match = re.search(r"(\d+[-~]\d+年|\d+年以上|应届|不限)", welfare_text)
                if exp_match:
                    experience = exp_match.group(1)

                # Parse education
                edu_match = re.search(r"(本科|大专|硕士|博士|高中|中专|学历不限)", welfare_text)
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
        """Save job listings to database."""
        saved_count = 0

        for job_data in jobs_data:
            try:
                job = Job(
                    data_source_id=self.data_source_id,
                    city_id=self.city_id,
                    crawl_task_id=UUID(self.config.get("task_id")) if self.config.get("task_id") else None,
                    source_id=job_data["source_id"],
                    source_url=job_data.get("source_url"),
                    title=job_data["title"],
                    company=job_data.get("company"),
                    district=job_data.get("district"),
                    salary_min=job_data.get("salary_min"),
                    salary_max=job_data.get("salary_max"),
                    salary_raw=job_data.get("salary_raw"),
                    experience=job_data.get("experience"),
                    education=job_data.get("education"),
                    tags=job_data.get("tags"),
                )
                db.add(job)
                saved_count += 1

            except Exception as e:
                logger.warning(f"Failed to save job: {e}")
                continue

        await db.commit()
        logger.info(f"Saved {saved_count} jobs to database")
        return saved_count
