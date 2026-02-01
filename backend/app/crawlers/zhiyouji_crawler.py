"""职友集薪资分位数爬虫实现."""
import logging
import re
from datetime import datetime
from decimal import Decimal
from typing import Callable, Awaitable
from urllib.parse import quote, urljoin

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.crawlers.base import BaseCrawler, RateLimiter
from app.models import Job, City, CompanyReview

logger = logging.getLogger(__name__)


class ZhiyoujiCrawler(BaseCrawler):
    """职友集薪资分位数爬虫.

    从职友集获取职位/公司的薪资分布数据，计算分位数。
    """

    BASE_URL = "https://www.jobui.com"

    def __init__(self, config: dict):
        super().__init__(config)
        self.db_session_factory = None
        # 职友集也有反爬，适当降低频率
        self.rate_limiter = RateLimiter(0.5)  # 每2秒1请求

    async def _init_db(self):
        """Initialize database connection."""
        engine = create_async_engine(settings.DATABASE_URL)
        self.db_session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

    async def _get_city_name(self, db: AsyncSession) -> str | None:
        """Get city name from ID."""
        if not self.city_id:
            return None

        result = await db.execute(select(City).where(City.id == self.city_id))
        city = result.scalar_one_or_none()
        return city.name if city else None

    async def _get_companies_to_crawl(
        self, db: AsyncSession, limit: int = 50
    ) -> list[str]:
        """Get distinct company names that need salary data.

        Args:
            db: Database session
            limit: Maximum number of companies

        Returns:
            List of company names
        """
        query = (
            select(Job.company)
            .where(
                Job.company.isnot(None),
                Job.company != "",
                Job.salary_percentile_50.is_(None),
            )
        )

        if self.city_id:
            query = query.where(Job.city_id == self.city_id)

        result = await db.execute(query.distinct().limit(limit))
        return [row[0] for row in result.all() if row[0]]

    async def crawl(
        self,
        on_progress: Callable[[int, int], Awaitable[None]] | None = None,
    ) -> dict:
        """Crawl salary statistics from 职友集.

        Args:
            on_progress: Callback for progress updates

        Returns:
            dict with crawl results
        """
        await self._init_db()

        max_companies = self.config.get("max_companies", 50)
        crawled_count = 0
        failed_count = 0

        async with self.db_session_factory() as db:
            # Get city name
            city_name = await self._get_city_name(db)
            if city_name:
                logger.info(f"Crawling salary data for city: {city_name}")

            # Get companies to crawl
            companies = await self._get_companies_to_crawl(db, limit=max_companies)

            if not companies:
                logger.info("No companies found that need salary data")
                return {"records_count": 0, "message": "No companies need salary data"}

            logger.info(f"Found {len(companies)} companies to crawl salary data for")
            total = len(companies)

            for i, company_name in enumerate(companies):
                try:
                    logger.info(f"[{i+1}/{total}] Getting salary data for: {company_name}")

                    # Search and get salary data
                    salary_data = await self._get_company_salary(company_name, city_name)

                    if salary_data:
                        # Update company_reviews
                        await self._update_company_review(db, company_name, salary_data)

                        # Update jobs with salary percentiles
                        await self._update_jobs_salary(db, company_name, salary_data)

                        crawled_count += 1
                        logger.info(
                            f"Saved salary data for {company_name}: "
                            f"P25={salary_data.get('salary_p25')}, "
                            f"P50={salary_data.get('salary_p50')}, "
                            f"P75={salary_data.get('salary_p75')}"
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

                # Rate limiting
                await self.wait_random(1.5, 3.0)

            await db.commit()

        return {
            "records_count": crawled_count,
            "total_companies": total,
            "failed_count": failed_count,
            "city": city_name,
        }

    async def _get_company_salary(
        self, company_name: str, city_name: str | None = None
    ) -> dict | None:
        """Get salary data for a company from 职友集.

        Args:
            company_name: Name of the company
            city_name: Optional city name for more specific search

        Returns:
            dict with salary percentile data or None
        """
        # Build search URL
        search_query = company_name
        if city_name:
            search_query = f"{company_name} {city_name}"

        search_url = f"{self.BASE_URL}/search.php?city=&key={quote(search_query)}&type=company"

        success = await self.goto_with_retry(search_url)
        if not success:
            return None

        # Wait for results
        await self.wait_for_selector_safe(".company-item, .search-company", timeout=10000)

        # Find company page
        company_url = await self._find_company_url(company_name)
        if not company_url:
            # Try to get salary from search results page
            return await self._parse_salary_from_search()

        # Navigate to company salary page
        salary_url = company_url.rstrip("/") + "/salary/"
        success = await self.goto_with_retry(salary_url)
        if not success:
            return None

        return await self._parse_salary_page(company_name)

    async def _find_company_url(self, company_name: str) -> str | None:
        """Find company detail page URL from search results."""
        selectors = [
            ".company-name a",
            ".company-item a",
            ".company-link",
            "a[href*='/company/']",
        ]

        for selector in selectors:
            try:
                links = await self.page.query_selector_all(selector)
                for link in links[:5]:  # Check first 5 results
                    text = await link.text_content()
                    if text and company_name.lower() in text.lower():
                        href = await link.get_attribute("href")
                        if href:
                            if href.startswith("/"):
                                return urljoin(self.BASE_URL, href)
                            return href
            except Exception:
                continue

        return None

    async def _parse_salary_from_search(self) -> dict | None:
        """Parse salary data from search results page."""
        # Try to find salary info in search results
        salary_el = await self.page.query_selector(
            ".salary-info, .avg-salary, [class*='salary']"
        )
        if not salary_el:
            return None

        text = await salary_el.text_content()
        if not text:
            return None

        # Parse salary value
        salary = self._parse_salary_value(text)
        if salary:
            # Estimate percentiles from average
            return {
                "salary_p25": Decimal(str(round(salary * 0.75, 2))),
                "salary_p50": Decimal(str(round(salary, 2))),
                "salary_p75": Decimal(str(round(salary * 1.25, 2))),
                "salary_sample_count": None,
            }

        return None

    async def _parse_salary_page(self, company_name: str) -> dict | None:
        """Parse salary data from company salary page."""
        await self.wait_for_selector_safe(
            ".salary-chart, .salary-distribution, .salary-info", timeout=10000
        )

        data = {}

        # Try to parse salary distribution chart data
        distribution = await self._parse_salary_distribution()
        if distribution:
            percentiles = self._calculate_percentiles(distribution)
            data.update(percentiles)

        # If no distribution, try to parse average/range
        if not data.get("salary_p50"):
            avg_salary = await self._parse_average_salary()
            if avg_salary:
                data["salary_p25"] = Decimal(str(round(avg_salary * 0.75, 2)))
                data["salary_p50"] = Decimal(str(round(avg_salary, 2)))
                data["salary_p75"] = Decimal(str(round(avg_salary * 1.25, 2)))

        # Parse sample count
        sample_count = await self._parse_sample_count()
        if sample_count:
            data["salary_sample_count"] = sample_count

        return data if data.get("salary_p50") else None

    async def _parse_salary_distribution(self) -> list[tuple[float, float]] | None:
        """Parse salary distribution data from chart.

        Returns:
            List of (salary_midpoint, percentage) tuples or None
        """
        # Look for distribution chart data
        # This could be in various formats depending on the page
        try:
            # Try to get chart data from JavaScript
            chart_data = await self.page.evaluate("""
                () => {
                    // Look for common chart data patterns
                    if (window.salaryData) return window.salaryData;
                    if (window.chartData) return window.chartData;

                    // Try to extract from chart elements
                    const bars = document.querySelectorAll('.chart-bar, .distribution-bar');
                    if (bars.length > 0) {
                        return Array.from(bars).map(bar => ({
                            value: parseFloat(bar.getAttribute('data-value') || bar.style.height || 0),
                            label: bar.getAttribute('data-label') || ''
                        }));
                    }
                    return null;
                }
            """)

            if chart_data and isinstance(chart_data, list):
                distribution = []
                for item in chart_data:
                    if isinstance(item, dict):
                        label = str(item.get("label", ""))
                        value = float(item.get("value", 0))
                        # Parse label like "8K-10K"
                        salary = self._parse_salary_range_midpoint(label)
                        if salary:
                            distribution.append((salary, value))

                if distribution:
                    return distribution

        except Exception as e:
            logger.debug(f"Failed to get chart data: {e}")

        # Fallback: parse from visible text
        try:
            bars = await self.page.query_selector_all(
                ".distribution-item, .salary-bar, .chart-item"
            )
            distribution = []

            for bar in bars:
                label = await bar.get_attribute("data-label")
                if not label:
                    label = await bar.text_content()

                value_str = await bar.get_attribute("data-value")
                if not value_str:
                    value_str = await bar.get_attribute("data-percent")

                if label:
                    salary = self._parse_salary_range_midpoint(label)
                    value = float(value_str) if value_str else 10  # Default weight
                    if salary:
                        distribution.append((salary, value))

            if distribution:
                return distribution

        except Exception as e:
            logger.debug(f"Failed to parse distribution bars: {e}")

        return None

    def _parse_salary_range_midpoint(self, text: str) -> float | None:
        """Parse salary range text and return midpoint value.

        Handles formats like:
        - "8K-10K"
        - "8000-10000"
        - "8-10千"
        - "1-1.5万"
        """
        if not text:
            return None

        text = text.replace(",", "").replace(" ", "")

        # Range pattern
        match = re.search(
            r"(\d+\.?\d*)\s*(K|k|千|万)?\s*[-~到至]\s*(\d+\.?\d*)\s*(K|k|千|万)?",
            text
        )
        if match:
            low = float(match.group(1))
            low_unit = match.group(2) or ""
            high = float(match.group(3))
            high_unit = match.group(4) or low_unit  # Use low unit if high has none

            # Apply unit multipliers correctly
            if low_unit.lower() in ["k", "千"]:
                low *= 1000
            elif low_unit == "万":
                low *= 10000

            if high_unit.lower() in ["k", "千"]:
                high *= 1000
            elif high_unit == "万":
                high *= 10000

            return (low + high) / 2

        # Single value
        match = re.search(r"(\d+\.?\d*)\s*(K|k|千|万)?", text)
        if match:
            val = float(match.group(1))
            unit = match.group(2) or ""
            if unit.lower() in ["k", "千"]:
                val *= 1000
            elif unit == "万":
                val *= 10000
            return val

        return None

    def _parse_salary_value(self, text: str) -> float | None:
        """Parse a single salary value."""
        return self._parse_salary_range_midpoint(text)

    def _calculate_percentiles(
        self, distribution: list[tuple[float, float]]
    ) -> dict:
        """Calculate P25, P50, P75 from distribution data.

        Args:
            distribution: List of (salary_midpoint, percentage/weight) tuples

        Returns:
            dict with salary_p25, salary_p50, salary_p75
        """
        if not distribution:
            return {}

        # Sort by salary
        distribution = sorted(distribution, key=lambda x: x[0])

        # Normalize weights to percentages
        total_weight = sum(w for _, w in distribution)
        if total_weight <= 0:
            return {}

        cumulative = 0
        p25 = p50 = p75 = None

        for salary, weight in distribution:
            prev_cumulative = cumulative
            cumulative += weight / total_weight * 100

            if p25 is None and cumulative >= 25:
                p25 = salary
            if p50 is None and cumulative >= 50:
                p50 = salary
            if p75 is None and cumulative >= 75:
                p75 = salary
                break

        # If we didn't find some percentiles, estimate
        if p50 is None and distribution:
            p50 = distribution[len(distribution) // 2][0]
        if p25 is None and p50:
            p25 = p50 * 0.8
        if p75 is None and p50:
            p75 = p50 * 1.2

        result = {}
        if p25:
            result["salary_p25"] = Decimal(str(round(p25, 2)))
        if p50:
            result["salary_p50"] = Decimal(str(round(p50, 2)))
        if p75:
            result["salary_p75"] = Decimal(str(round(p75, 2)))

        return result

    async def _parse_average_salary(self) -> float | None:
        """Parse average salary from page."""
        selectors = [
            ".avg-salary",
            ".average-salary",
            ".salary-avg",
            "[class*='avg'] .value",
            ".salary-value",
        ]

        for selector in selectors:
            text = await self.safe_get_text(selector)
            if text:
                salary = self._parse_salary_value(text)
                if salary and 1000 <= salary <= 500000:  # Sanity check
                    return salary

        return None

    async def _parse_sample_count(self) -> int | None:
        """Parse sample count from page."""
        selectors = [
            ".sample-count",
            ".salary-count",
            ".data-count",
            "[class*='sample'] .num",
        ]

        for selector in selectors:
            text = await self.safe_get_text(selector)
            if text:
                match = re.search(r"(\d+)", text.replace(",", ""))
                if match:
                    return int(match.group(1))

        return None

    async def _update_company_review(
        self, db: AsyncSession, company_name: str, salary_data: dict
    ):
        """Update or insert company_reviews with salary data."""
        # Check if exists
        result = await db.execute(
            select(CompanyReview).where(CompanyReview.company_name == company_name)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing
            await db.execute(
                update(CompanyReview)
                .where(CompanyReview.company_name == company_name)
                .values(
                    salary_p25=salary_data.get("salary_p25"),
                    salary_p50=salary_data.get("salary_p50"),
                    salary_p75=salary_data.get("salary_p75"),
                    salary_sample_count=salary_data.get("salary_sample_count"),
                )
            )
        else:
            # Insert new
            stmt = insert(CompanyReview).values(
                company_name=company_name,
                data_source_id=self.data_source_id,
                salary_p25=salary_data.get("salary_p25"),
                salary_p50=salary_data.get("salary_p50"),
                salary_p75=salary_data.get("salary_p75"),
                salary_sample_count=salary_data.get("salary_sample_count"),
            )
            await db.execute(stmt)

    async def _update_jobs_salary(
        self, db: AsyncSession, company_name: str, salary_data: dict
    ):
        """Update jobs table with salary percentiles."""
        await db.execute(
            update(Job)
            .where(Job.company == company_name)
            .values(
                salary_percentile_25=salary_data.get("salary_p25"),
                salary_percentile_50=salary_data.get("salary_p50"),
                salary_percentile_75=salary_data.get("salary_p75"),
            )
        )
