"""58同城租房爬虫实现."""
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
from app.models import Rent, City

logger = logging.getLogger(__name__)

# 58同城城市代码映射（与 job_crawler 共用）
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


class RentCrawler(BaseCrawler):
    """58同城租房页面爬虫."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.db_session_factory = None
        self.rents_collected = []

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

    def _parse_price(self, price_text: str) -> Decimal | None:
        """Parse price text like '2500元/月' into decimal value."""
        if not price_text:
            return None

        # Clean the text
        price_text = price_text.replace(",", "").replace(" ", "")

        # Pattern for price: "2500元/月" or "2500"
        match = re.search(r"(\d+(?:\.\d+)?)", price_text)
        if match:
            return Decimal(match.group(1))

        return None

    def _parse_area(self, area_text: str) -> Decimal | None:
        """Parse area text like '50㎡' into decimal value."""
        if not area_text:
            return None

        # Pattern for area: "50㎡" or "50平米"
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:㎡|平米|平方米|m²)?", area_text)
        if match:
            return Decimal(match.group(1))

        return None

    async def crawl(
        self,
        on_progress: Callable[[int, int], Awaitable[None]] | None = None,
    ) -> dict:
        """Crawl 58同城 rental listings.

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
            logger.info(f"Starting rent crawl for {city_name} (code: {city_code})")

            # Build URL for rental listings
            # 58同城租房页面: https://{city_code}.58.com/chuzu/
            url = f"https://{city_code}.58.com/chuzu/"

            logger.info(f"Crawling URL: {url}")

            # Navigate to page
            success = await self.goto_with_retry(url)
            if not success:
                raise Exception(f"Failed to load page: {url}")

            # Wait for rental listings to load
            await self.wait_for_selector_safe(".house-list li, .list-item", timeout=15000)

            # Scroll to load more content
            await self.scroll_page(scroll_count=3)

            # Parse rental listings
            rents_data = await self._parse_rent_list()

            if on_progress:
                await on_progress(50, len(rents_data))

            # Save to database
            saved_count = await self._save_rents(db, rents_data, city_name)

            if on_progress:
                await on_progress(100, saved_count)

            return {
                "records_count": saved_count,
                "city": city_name,
                "total_found": len(rents_data),
            }

    async def _parse_rent_list(self) -> list[dict]:
        """Parse rental listings from the current page."""
        rents = []

        # Try different selectors for 58同城 rental listings
        selectors = [
            ".house-list li",
            ".list-item",
            "[class*='house'] li",
            ".property-list li",
        ]

        items = []
        for selector in selectors:
            items = await self.page.query_selector_all(selector)
            if items:
                logger.info(f"Found {len(items)} rent items with selector: {selector}")
                break

        if not items:
            logger.warning("No rental listings found on page")
            # Take a screenshot for debugging
            await self.page.screenshot(path="debug_rent_page.png")
            return rents

        for item in items:
            try:
                rent_data = await self._parse_rent_item(item)
                if rent_data:
                    rents.append(rent_data)
            except Exception as e:
                logger.warning(f"Failed to parse rent item: {e}")
                continue

        logger.info(f"Parsed {len(rents)} rental listings")
        return rents

    async def _parse_rent_item(self, item) -> dict | None:
        """Parse a single rental listing element."""
        try:
            # Extract title and link
            title_el = await item.query_selector(
                "a.title, .des h2 a, .house-title a, a[href*='chuzu']"
            )
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
                source_id = f"58rent_{hash(title)}"

            # Extract price
            price_el = await item.query_selector(
                ".price, .money, [class*='price'], [class*='money']"
            )
            price_raw = ""
            if price_el:
                price_raw = await price_el.text_content()
                price_raw = price_raw.strip() if price_raw else ""

            price = self._parse_price(price_raw)

            # Extract property type (整租/合租)
            property_type = ""
            type_el = await item.query_selector(".type, .tag, [class*='type']")
            if type_el:
                type_text = await type_el.text_content()
                if type_text:
                    if "整租" in type_text:
                        property_type = "整租"
                    elif "合租" in type_text:
                        property_type = "合租"
                    elif "公寓" in type_text:
                        property_type = "公寓"

            # Extract location/district
            area_el = await item.query_selector(
                ".add, .area, [class*='area'], [class*='address']"
            )
            district = ""
            neighborhood = ""
            if area_el:
                area_text = await area_el.text_content()
                area_text = area_text.strip() if area_text else ""
                # Usually format like "福田-车公庙" or "南山区 科技园"
                parts = re.split(r"[-\s·]", area_text)
                if len(parts) >= 1:
                    district = parts[0].strip()
                if len(parts) >= 2:
                    neighborhood = parts[1].strip()

            # Extract layout (户型) like "2室1厅1卫"
            layout = ""
            layout_el = await item.query_selector(
                ".room, .layout, [class*='room'], [class*='layout']"
            )
            if layout_el:
                layout = await layout_el.text_content()
                layout = layout.strip() if layout else ""
            else:
                # Try to extract from title
                layout_match = re.search(r"(\d室\d厅\d?卫?)", title)
                if layout_match:
                    layout = layout_match.group(1)

            # Extract area (面积)
            area_raw = ""
            area_value = None
            size_el = await item.query_selector(
                ".area-size, .size, [class*='area']"
            )
            if size_el:
                area_raw = await size_el.text_content()
                area_raw = area_raw.strip() if area_raw else ""
                area_value = self._parse_area(area_raw)

            # Extract subway info
            subway_el = await item.query_selector(
                ".subway, .traffic, [class*='subway'], [class*='metro']"
            )
            subway_info = ""
            if subway_el:
                subway_info = await subway_el.text_content()
                subway_info = subway_info.strip() if subway_info else ""

            # Extract tags/facilities
            tags_el = await item.query_selector_all(
                ".tag span, .tags span, [class*='tag'] span, .icons span"
            )
            facilities = []
            for tag_el in tags_el[:8]:  # Limit to 8 tags
                tag_text = await tag_el.text_content()
                if tag_text:
                    facilities.append(tag_text.strip())

            return {
                "source_id": source_id,
                "source_url": source_url,
                "title": title,
                "property_type": property_type,
                "district": district,
                "neighborhood": neighborhood,
                "price": price,
                "price_raw": price_raw,
                "area": area_value,
                "area_raw": area_raw,
                "layout": layout,
                "subway_info": subway_info,
                "facilities": ",".join(facilities) if facilities else None,
            }

        except Exception as e:
            logger.warning(f"Error parsing rent item: {e}")
            return None

    async def _save_rents(
        self, db: AsyncSession, rents_data: list[dict], city_name: str
    ) -> int:
        """Save rental listings to database."""
        saved_count = 0

        for rent_data in rents_data:
            try:
                rent = Rent(
                    data_source_id=self.data_source_id,
                    city_id=self.city_id,
                    crawl_task_id=UUID(self.config.get("task_id")) if self.config.get("task_id") else None,
                    source_id=rent_data["source_id"],
                    source_url=rent_data.get("source_url"),
                    title=rent_data["title"],
                    property_type=rent_data.get("property_type"),
                    district=rent_data.get("district"),
                    neighborhood=rent_data.get("neighborhood"),
                    price=rent_data.get("price"),
                    price_raw=rent_data.get("price_raw"),
                    area=rent_data.get("area"),
                    area_raw=rent_data.get("area_raw"),
                    layout=rent_data.get("layout"),
                    subway_info=rent_data.get("subway_info"),
                    facilities=rent_data.get("facilities"),
                )
                db.add(rent)
                saved_count += 1

            except Exception as e:
                logger.warning(f"Failed to save rent: {e}")
                continue

        await db.commit()
        logger.info(f"Saved {saved_count} rental listings to database")
        return saved_count
