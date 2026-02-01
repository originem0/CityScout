"""看准网公司评分爬虫实现."""
import hashlib
import logging
import re
from datetime import datetime
from decimal import Decimal
from typing import Callable, Awaitable
from urllib.parse import quote, urljoin

from sqlalchemy import select, update, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.crawlers.base import BaseCrawler, RateLimiter
from app.models import Job, CompanyReview

logger = logging.getLogger(__name__)


class KanzhunCrawler(BaseCrawler):
    """看准网公司评分爬虫.

    从 jobs 表获取公司列表，在看准网搜索并获取公司评分数据。
    """

    BASE_URL = "https://www.kanzhun.com"
    SEARCH_URL = "https://www.kanzhun.com/search/"

    def __init__(self, config: dict):
        super().__init__(config)
        self.db_session_factory = None
        # 看准网反爬较严格，降低请求频率
        self.rate_limiter = RateLimiter(0.3)  # 每3秒1请求

    async def _init_db(self):
        """Initialize database connection."""
        engine = create_async_engine(settings.DATABASE_URL)
        self.db_session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

    async def _get_companies_to_crawl(self, db: AsyncSession, limit: int = 50) -> list[str]:
        """Get distinct company names that don't have ratings yet.

        Args:
            db: Database session
            limit: Maximum number of companies to crawl

        Returns:
            List of company names
        """
        # 获取没有评分的公司名称
        result = await db.execute(
            select(Job.company)
            .where(
                Job.company.isnot(None),
                Job.company != "",
                Job.company_rating.is_(None),
            )
            .distinct()
            .limit(limit)
        )
        companies = [row[0] for row in result.all() if row[0]]
        return companies

    async def crawl(
        self,
        on_progress: Callable[[int, int], Awaitable[None]] | None = None,
    ) -> dict:
        """Crawl company ratings from 看准网.

        Args:
            on_progress: Callback for progress updates (progress%, record_count)

        Returns:
            dict with crawl results
        """
        await self._init_db()

        max_companies = self.config.get("max_companies", 50)
        crawled_count = 0
        failed_count = 0

        async with self.db_session_factory() as db:
            # Get companies to crawl
            companies = await self._get_companies_to_crawl(db, limit=max_companies)

            if not companies:
                logger.info("No companies found that need ratings")
                return {"records_count": 0, "message": "No companies need ratings"}

            logger.info(f"Found {len(companies)} companies to crawl ratings for")

            total = len(companies)

            for i, company_name in enumerate(companies):
                try:
                    logger.info(f"[{i+1}/{total}] Searching for: {company_name}")

                    # Search for company
                    company_url = await self._search_company(company_name)

                    if not company_url:
                        logger.warning(f"Company not found: {company_name}")
                        failed_count += 1
                        continue

                    # Parse ratings from company page
                    rating_data = await self._parse_company_ratings(company_url, company_name)

                    if rating_data:
                        # Save to company_reviews
                        await self._save_company_review(db, rating_data)

                        # Update jobs with this company
                        await self._update_jobs_rating(
                            db, company_name, rating_data.get("overall_rating")
                        )

                        crawled_count += 1
                        logger.info(
                            f"Saved rating for {company_name}: {rating_data.get('overall_rating')}"
                        )
                    else:
                        failed_count += 1

                except Exception as e:
                    logger.error(f"Error crawling {company_name}: {e}")
                    failed_count += 1

                # Report progress
                if on_progress:
                    progress_pct = int(((i + 1) / total) * 100)
                    await on_progress(progress_pct, crawled_count)

                # Rate limiting between companies
                await self.wait_random(2.0, 4.0)

            await db.commit()

        return {
            "records_count": crawled_count,
            "total_companies": total,
            "failed_count": failed_count,
        }

    async def _search_company(self, company_name: str) -> str | None:
        """Search for company on 看准网.

        Args:
            company_name: Name of the company to search

        Returns:
            URL of company detail page or None if not found
        """
        search_url = f"{self.SEARCH_URL}?type=company&q={quote(company_name)}"

        success = await self.goto_with_retry(search_url)
        if not success:
            return None

        # Wait for search results
        await self.wait_for_selector_safe(".company-item, .search-result-item", timeout=10000)

        # Find first matching company
        selectors = [
            ".company-item a",
            ".search-result-item a",
            ".company-info a",
            "a[href*='/gsr']",
            "a[href*='/company']",
        ]

        for selector in selectors:
            try:
                link = await self.page.query_selector(selector)
                if link:
                    href = await link.get_attribute("href")
                    if href:
                        # Make absolute URL
                        if href.startswith("/"):
                            return urljoin(self.BASE_URL, href)
                        elif href.startswith("http"):
                            return href
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue

        return None

    async def _parse_company_ratings(
        self, company_url: str, company_name: str
    ) -> dict | None:
        """Parse company ratings from detail page.

        Args:
            company_url: URL of company detail page
            company_name: Name of the company

        Returns:
            dict with rating data or None if parsing failed
        """
        success = await self.goto_with_retry(company_url)
        if not success:
            return None

        # Wait for ratings to load
        await self.wait_for_selector_safe(".score, .rating, [class*='score']", timeout=10000)

        try:
            data = {
                "company_name": company_name,
                "data_source_id": self.data_source_id,
                "source_url": company_url,
                "crawled_at": datetime.now(),
            }

            # Parse overall rating (通常在页面顶部)
            overall = await self._parse_rating_value(
                ".company-score .score-num, .overall-score, .score-value"
            )
            if overall:
                data["overall_rating"] = overall

            # Parse sub-ratings (看准网通常有这些维度)
            rating_selectors = {
                "culture_rating": ".culture-score, [data-type='culture'] .score",
                "management_rating": ".management-score, [data-type='management'] .score",
                "salary_benefit_rating": ".salary-score, [data-type='salary'] .score",
                "career_rating": ".career-score, [data-type='career'] .score",
                "work_life_balance": ".balance-score, [data-type='balance'] .score",
            }

            for field, selector in rating_selectors.items():
                value = await self._parse_rating_value(selector)
                if value:
                    data[field] = value

            # Parse review count
            review_count = await self._parse_count(".review-count, .comment-count")
            if review_count:
                data["review_count"] = review_count

            # Parse recommend rate
            recommend = await self._parse_percentage(".recommend-rate, .recommend")
            if recommend:
                data["recommend_rate"] = recommend

            # Parse company info
            summary = await self.safe_get_text(".company-intro, .company-summary, .intro")
            if summary:
                data["company_summary"] = summary[:2000]  # Limit length

            industry = await self.safe_get_text(".company-industry, .industry, .tag-industry")
            if industry:
                data["industry"] = industry[:100]

            # Calculate match confidence
            data["match_confidence"] = self._calculate_match_confidence(
                company_name, await self.safe_get_text(".company-name, .name, h1")
            )

            return data if data.get("overall_rating") else None

        except Exception as e:
            logger.error(f"Error parsing ratings for {company_name}: {e}")
            return None

    async def _parse_rating_value(self, selector: str) -> Decimal | None:
        """Parse a rating value from page."""
        text = await self.safe_get_text(selector)
        if text:
            # Extract decimal number
            match = re.search(r"(\d+\.?\d*)", text)
            if match:
                try:
                    value = float(match.group(1))
                    if 0 <= value <= 5:
                        return Decimal(str(round(value, 2)))
                except (ValueError, TypeError):
                    pass
        return None

    async def _parse_count(self, selector: str) -> int | None:
        """Parse a count value from page."""
        text = await self.safe_get_text(selector)
        if text:
            # Extract integer, handle "1.2k" format
            match = re.search(r"(\d+\.?\d*)\s*(k|K|万)?", text)
            if match:
                try:
                    value = float(match.group(1))
                    unit = match.group(2)
                    if unit and unit.lower() == "k":
                        value *= 1000
                    elif unit == "万":
                        value *= 10000
                    return int(value)
                except (ValueError, TypeError):
                    pass
        return None

    async def _parse_percentage(self, selector: str) -> Decimal | None:
        """Parse a percentage value from page."""
        text = await self.safe_get_text(selector)
        if text:
            match = re.search(r"(\d+\.?\d*)%?", text)
            if match:
                try:
                    value = float(match.group(1))
                    if 0 <= value <= 100:
                        return Decimal(str(round(value, 2)))
                except (ValueError, TypeError):
                    pass
        return None

    def _calculate_match_confidence(
        self, query_name: str, found_name: str
    ) -> Decimal:
        """Calculate confidence score for company name match.

        Args:
            query_name: The company name we searched for
            found_name: The company name found on the page

        Returns:
            Confidence score 0.00-1.00
        """
        if not found_name:
            return Decimal("0.50")

        query_clean = query_name.lower().strip()
        found_clean = found_name.lower().strip()

        # Exact match
        if query_clean == found_clean:
            return Decimal("1.00")

        # One contains the other
        if query_clean in found_clean or found_clean in query_clean:
            return Decimal("0.90")

        # Calculate word overlap
        query_words = set(query_clean.split())
        found_words = set(found_clean.split())
        overlap = len(query_words & found_words)
        total = len(query_words | found_words)

        if total > 0:
            return Decimal(str(round(overlap / total, 2)))

        return Decimal("0.50")

    async def _save_company_review(self, db: AsyncSession, data: dict):
        """Save company review to database with upsert."""
        stmt = insert(CompanyReview).values(**data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["company_name"],
            set_={
                k: getattr(stmt.excluded, k)
                for k in data.keys()
                if k not in ["company_name", "data_source_id"]
            },
        )
        await db.execute(stmt)

    async def _update_jobs_rating(
        self, db: AsyncSession, company_name: str, rating: Decimal | None
    ):
        """Update company_rating for all jobs with this company name."""
        if rating is None:
            return

        await db.execute(
            update(Job)
            .where(Job.company == company_name)
            .values(company_rating=rating)
        )
