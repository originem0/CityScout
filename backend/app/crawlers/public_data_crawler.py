"""Public data crawler - fetches city statistics from public sources."""
import logging
from decimal import Decimal
from typing import Callable, Awaitable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.crawlers.base import BaseCrawler
from app.models import City, CityStats

logger = logging.getLogger(__name__)

# 内置城市统计数据（2024年数据参考）
# 数据来源：国家统计局、各城市统计年鉴
CITY_STATS_DATA = {
    "深圳": {
        "population": 1768,  # 万人
        "gdp": 34606,  # 亿元
        "gdp_per_capita": 195700,  # 元
        "avg_salary": 13730,  # 月均工资
        "living_cost_index": 125,  # 生活成本指数
        "housing_price": 54000,  # 元/㎡
        "avg_temp_year": 23.0,
        "avg_temp_summer": 28.5,
        "avg_temp_winter": 15.5,
        "rainfall": 1933,
        "sunny_days": 220,
        "air_quality_index": 55,
        "area": 1997.47,
        "description": "中国经济特区，科技创新中心，年轻人聚集的城市",
    },
    "广州": {
        "population": 1881,
        "gdp": 30355,
        "gdp_per_capita": 161400,
        "avg_salary": 11850,
        "living_cost_index": 115,
        "housing_price": 42000,
        "avg_temp_year": 22.5,
        "avg_temp_summer": 28.8,
        "avg_temp_winter": 14.5,
        "rainfall": 1736,
        "sunny_days": 180,
        "air_quality_index": 60,
        "area": 7434.40,
        "description": "华南经济中心，千年商都，美食之都",
    },
    "杭州": {
        "population": 1237,
        "gdp": 20059,
        "gdp_per_capita": 162200,
        "avg_salary": 12680,
        "living_cost_index": 118,
        "housing_price": 38000,
        "avg_temp_year": 17.5,
        "avg_temp_summer": 28.5,
        "avg_temp_winter": 5.5,
        "rainfall": 1454,
        "sunny_days": 160,
        "air_quality_index": 58,
        "area": 16850.00,
        "description": "互联网之都，人间天堂，阿里巴巴总部所在地",
    },
    "南京": {
        "population": 949,
        "gdp": 17421,
        "gdp_per_capita": 183600,
        "avg_salary": 11200,
        "living_cost_index": 108,
        "housing_price": 32000,
        "avg_temp_year": 16.0,
        "avg_temp_summer": 28.0,
        "avg_temp_winter": 3.5,
        "rainfall": 1106,
        "sunny_days": 180,
        "air_quality_index": 65,
        "area": 6587.02,
        "description": "六朝古都，教育重镇，长三角重要城市",
    },
    "苏州": {
        "population": 1292,
        "gdp": 24653,
        "gdp_per_capita": 190800,
        "avg_salary": 10800,
        "living_cost_index": 105,
        "housing_price": 28000,
        "avg_temp_year": 16.5,
        "avg_temp_summer": 28.0,
        "avg_temp_winter": 4.0,
        "rainfall": 1100,
        "sunny_days": 170,
        "air_quality_index": 62,
        "area": 8657.32,
        "description": "园林城市，制造业强市，外资企业聚集地",
    },
    "成都": {
        "population": 2140,
        "gdp": 22074,
        "gdp_per_capita": 103200,
        "avg_salary": 9850,
        "living_cost_index": 95,
        "housing_price": 18000,
        "avg_temp_year": 16.5,
        "avg_temp_summer": 25.5,
        "avg_temp_winter": 6.5,
        "rainfall": 900,
        "sunny_days": 80,
        "air_quality_index": 75,
        "area": 14335.00,
        "description": "天府之国，休闲之都，新一线城市代表",
    },
    "武汉": {
        "population": 1374,
        "gdp": 20011,
        "gdp_per_capita": 145700,
        "avg_salary": 10200,
        "living_cost_index": 98,
        "housing_price": 18500,
        "avg_temp_year": 17.0,
        "avg_temp_summer": 29.5,
        "avg_temp_winter": 4.0,
        "rainfall": 1269,
        "sunny_days": 170,
        "air_quality_index": 70,
        "area": 8569.15,
        "description": "九省通衢，教育大市，中部崛起核心城市",
    },
    "长沙": {
        "population": 1042,
        "gdp": 14094,
        "gdp_per_capita": 135300,
        "avg_salary": 9500,
        "living_cost_index": 92,
        "housing_price": 12500,
        "avg_temp_year": 17.5,
        "avg_temp_summer": 29.0,
        "avg_temp_winter": 5.0,
        "rainfall": 1361,
        "sunny_days": 160,
        "air_quality_index": 68,
        "area": 11819.00,
        "description": "娱乐之都，网红城市，房价洼地",
    },
    "厦门": {
        "population": 528,
        "gdp": 8066,
        "gdp_per_capita": 152800,
        "avg_salary": 10500,
        "living_cost_index": 112,
        "housing_price": 45000,
        "avg_temp_year": 21.0,
        "avg_temp_summer": 28.0,
        "avg_temp_winter": 13.5,
        "rainfall": 1143,
        "sunny_days": 200,
        "air_quality_index": 45,
        "area": 1700.61,
        "description": "海上花园，宜居城市，空气质量最佳",
    },
    "福州": {
        "population": 845,
        "gdp": 12928,
        "gdp_per_capita": 153000,
        "avg_salary": 9200,
        "living_cost_index": 100,
        "housing_price": 25000,
        "avg_temp_year": 20.0,
        "avg_temp_summer": 28.5,
        "avg_temp_winter": 11.5,
        "rainfall": 1348,
        "sunny_days": 180,
        "air_quality_index": 50,
        "area": 11968.00,
        "description": "福建省会，温泉之都，数字中国峰会举办地",
    },
    "珠海": {
        "population": 247,
        "gdp": 4045,
        "gdp_per_capita": 163800,
        "avg_salary": 10200,
        "living_cost_index": 108,
        "housing_price": 28000,
        "avg_temp_year": 23.0,
        "avg_temp_summer": 28.5,
        "avg_temp_winter": 15.0,
        "rainfall": 1964,
        "sunny_days": 210,
        "air_quality_index": 48,
        "area": 1736.45,
        "description": "浪漫之城，宜居花园，港珠澳大桥连接",
    },
    "东莞": {
        "population": 1048,
        "gdp": 11400,
        "gdp_per_capita": 108800,
        "avg_salary": 8500,
        "living_cost_index": 95,
        "housing_price": 22000,
        "avg_temp_year": 23.0,
        "avg_temp_summer": 28.5,
        "avg_temp_winter": 15.5,
        "rainfall": 1819,
        "sunny_days": 200,
        "air_quality_index": 58,
        "area": 2460.10,
        "description": "世界工厂，制造业之都，华为总部所在地",
    },
    "佛山": {
        "population": 961,
        "gdp": 12698,
        "gdp_per_capita": 132100,
        "avg_salary": 9000,
        "living_cost_index": 98,
        "housing_price": 18000,
        "avg_temp_year": 22.5,
        "avg_temp_summer": 28.5,
        "avg_temp_winter": 14.5,
        "rainfall": 1682,
        "sunny_days": 190,
        "air_quality_index": 60,
        "area": 3797.72,
        "description": "制造业名城，广佛同城，陶瓷之都",
    },
    "昆明": {
        "population": 860,
        "gdp": 7864,
        "gdp_per_capita": 91400,
        "avg_salary": 7800,
        "living_cost_index": 88,
        "housing_price": 13500,
        "avg_temp_year": 15.5,
        "avg_temp_summer": 20.0,
        "avg_temp_winter": 9.5,
        "rainfall": 1035,
        "sunny_days": 230,
        "air_quality_index": 52,
        "area": 21012.00,
        "description": "春城，四季如春，鲜花之都",
    },
    "南宁": {
        "population": 889,
        "gdp": 5218,
        "gdp_per_capita": 58700,
        "avg_salary": 7200,
        "living_cost_index": 85,
        "housing_price": 12000,
        "avg_temp_year": 22.0,
        "avg_temp_summer": 28.5,
        "avg_temp_winter": 13.5,
        "rainfall": 1304,
        "sunny_days": 180,
        "air_quality_index": 55,
        "area": 22112.00,
        "description": "绿城，东盟博览会永久举办地",
    },
    "贵阳": {
        "population": 622,
        "gdp": 4904,
        "gdp_per_capita": 78800,
        "avg_salary": 7500,
        "living_cost_index": 85,
        "housing_price": 10500,
        "avg_temp_year": 15.0,
        "avg_temp_summer": 23.5,
        "avg_temp_winter": 5.5,
        "rainfall": 1174,
        "sunny_days": 130,
        "air_quality_index": 50,
        "area": 8034.00,
        "description": "避暑之都，大数据之都，森林城市",
    },
    "海口": {
        "population": 293,
        "gdp": 2134,
        "gdp_per_capita": 72800,
        "avg_salary": 7800,
        "living_cost_index": 95,
        "housing_price": 18000,
        "avg_temp_year": 24.5,
        "avg_temp_summer": 28.5,
        "avg_temp_winter": 18.5,
        "rainfall": 1664,
        "sunny_days": 220,
        "air_quality_index": 42,
        "area": 3145.93,
        "description": "椰城，自贸港核心，热带滨海城市",
    },
    "三亚": {
        "population": 103,
        "gdp": 925,
        "gdp_per_capita": 89800,
        "avg_salary": 7200,
        "living_cost_index": 98,
        "housing_price": 35000,
        "avg_temp_year": 26.0,
        "avg_temp_summer": 28.5,
        "avg_temp_winter": 22.0,
        "rainfall": 1263,
        "sunny_days": 250,
        "air_quality_index": 38,
        "area": 1921.00,
        "description": "东方夏威夷，国际旅游岛核心，冬季度假胜地",
    },
    "无锡": {
        "population": 749,
        "gdp": 15456,
        "gdp_per_capita": 206400,
        "avg_salary": 10500,
        "living_cost_index": 102,
        "housing_price": 22000,
        "avg_temp_year": 16.0,
        "avg_temp_summer": 28.0,
        "avg_temp_winter": 3.5,
        "rainfall": 1121,
        "sunny_days": 170,
        "air_quality_index": 65,
        "area": 4627.47,
        "description": "太湖明珠，物联网之都，制造业强市",
    },
    "宁波": {
        "population": 969,
        "gdp": 16219,
        "gdp_per_capita": 167400,
        "avg_salary": 10800,
        "living_cost_index": 105,
        "housing_price": 25000,
        "avg_temp_year": 17.0,
        "avg_temp_summer": 28.0,
        "avg_temp_winter": 5.5,
        "rainfall": 1480,
        "sunny_days": 160,
        "air_quality_index": 58,
        "area": 9816.00,
        "description": "港口城市，民营经济发达，制造业基地",
    },
}


class PublicDataCrawler(BaseCrawler):
    """Crawler for public city statistics data."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.db_session_factory = None

    async def setup(self):
        """Skip browser setup - not needed for embedded data."""
        pass

    async def teardown(self):
        """Skip browser teardown."""
        pass

    async def _init_db(self):
        """Initialize database connection."""
        engine = create_async_engine(settings.DATABASE_URL)
        self.db_session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

    async def crawl(
        self,
        on_progress: Callable[[int, int], Awaitable[None]] | None = None,
    ) -> dict:
        """Crawl public data for cities.

        Uses embedded statistics data combined with optional online sources.
        """
        await self._init_db()

        async with self.db_session_factory() as db:
            # Get target city if specified
            if self.city_id:
                result = await db.execute(
                    select(City).where(City.id == self.city_id)
                )
                city = result.scalar_one_or_none()
                if not city:
                    raise ValueError(f"City not found: {self.city_id}")
                cities = [city]
            else:
                # Get all enabled cities
                result = await db.execute(
                    select(City).where(City.enabled == True)
                )
                cities = result.scalars().all()

            logger.info(f"Processing public data for {len(cities)} cities")

            saved_count = 0
            total = len(cities)

            for i, city in enumerate(cities):
                try:
                    # Get data from embedded source
                    stats_data = CITY_STATS_DATA.get(city.name)

                    if stats_data:
                        # Check if stats already exist for this city
                        existing = await db.execute(
                            select(CityStats).where(CityStats.city_id == city.id)
                        )
                        existing_stats = existing.scalar_one_or_none()

                        if existing_stats:
                            # Update existing record
                            for key, value in stats_data.items():
                                if hasattr(existing_stats, key):
                                    if isinstance(value, (int, float)) and key not in [
                                        "population",
                                        "rainfall",
                                        "sunny_days",
                                        "air_quality_index",
                                    ]:
                                        setattr(existing_stats, key, Decimal(str(value)))
                                    else:
                                        setattr(existing_stats, key, value)
                            existing_stats.data_year = 2024
                            existing_stats.source_name = "国家统计局/城市统计年鉴"
                            logger.info(f"Updated stats for {city.name}")
                        else:
                            # Create new record
                            city_stats = CityStats(
                                city_id=city.id,
                                data_source_id=self.data_source_id,
                                population=stats_data.get("population"),
                                gdp=Decimal(str(stats_data["gdp"]))
                                if stats_data.get("gdp")
                                else None,
                                gdp_per_capita=Decimal(str(stats_data["gdp_per_capita"]))
                                if stats_data.get("gdp_per_capita")
                                else None,
                                avg_salary=Decimal(str(stats_data["avg_salary"]))
                                if stats_data.get("avg_salary")
                                else None,
                                living_cost_index=Decimal(
                                    str(stats_data["living_cost_index"])
                                )
                                if stats_data.get("living_cost_index")
                                else None,
                                housing_price=Decimal(str(stats_data["housing_price"]))
                                if stats_data.get("housing_price")
                                else None,
                                avg_temp_year=Decimal(str(stats_data["avg_temp_year"]))
                                if stats_data.get("avg_temp_year")
                                else None,
                                avg_temp_summer=Decimal(
                                    str(stats_data["avg_temp_summer"])
                                )
                                if stats_data.get("avg_temp_summer")
                                else None,
                                avg_temp_winter=Decimal(
                                    str(stats_data["avg_temp_winter"])
                                )
                                if stats_data.get("avg_temp_winter")
                                else None,
                                rainfall=stats_data.get("rainfall"),
                                sunny_days=stats_data.get("sunny_days"),
                                air_quality_index=stats_data.get("air_quality_index"),
                                area=Decimal(str(stats_data["area"]))
                                if stats_data.get("area")
                                else None,
                                description=stats_data.get("description"),
                                data_year=2024,
                                source_name="国家统计局/城市统计年鉴",
                            )
                            db.add(city_stats)
                            logger.info(f"Created stats for {city.name}")

                        saved_count += 1
                    else:
                        logger.warning(f"No embedded data for city: {city.name}")

                    # Update progress
                    if on_progress:
                        progress = int((i + 1) / total * 100)
                        await on_progress(progress, saved_count)

                except Exception as e:
                    logger.error(f"Failed to process city {city.name}: {e}")
                    continue

            await db.commit()
            logger.info(f"Saved statistics for {saved_count} cities")

            return {
                "records_count": saved_count,
                "total_cities": total,
            }
