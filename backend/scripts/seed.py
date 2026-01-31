"""
Seed script to populate initial data for CityScout.
Run with: python -m scripts.seed
"""
import asyncio
from sqlalchemy import select
from app.database import async_session
from app.models import City, Keyword, DataSource


# 南方城市数据
CITIES = [
    # 一线城市
    {"name": "深圳", "province": "广东", "tier": "tier1"},
    {"name": "广州", "province": "广东", "tier": "tier1"},
    # 新一线城市
    {"name": "杭州", "province": "浙江", "tier": "new_tier1"},
    {"name": "成都", "province": "四川", "tier": "new_tier1"},
    {"name": "重庆", "province": "重庆", "tier": "new_tier1"},
    {"name": "武汉", "province": "湖北", "tier": "new_tier1"},
    {"name": "苏州", "province": "江苏", "tier": "new_tier1"},
    {"name": "南京", "province": "江苏", "tier": "new_tier1"},
    {"name": "长沙", "province": "湖南", "tier": "new_tier1"},
    {"name": "东莞", "province": "广东", "tier": "new_tier1"},
    # 二线城市
    {"name": "佛山", "province": "广东", "tier": "tier2"},
    {"name": "珠海", "province": "广东", "tier": "tier2"},
    {"name": "厦门", "province": "福建", "tier": "tier2"},
    {"name": "福州", "province": "福建", "tier": "tier2"},
    {"name": "昆明", "province": "云南", "tier": "tier2"},
    {"name": "南宁", "province": "广西", "tier": "tier2"},
    {"name": "贵阳", "province": "贵州", "tier": "tier2"},
    {"name": "海口", "province": "海南", "tier": "tier2"},
    {"name": "无锡", "province": "江苏", "tier": "tier2"},
    {"name": "宁波", "province": "浙江", "tier": "tier2"},
]

# 搜索关键词
KEYWORDS = [
    # 招聘搜索关键词 - 核心
    {"category": "job_search", "keyword": "Python", "priority": "core"},
    {"category": "job_search", "keyword": "后端开发", "priority": "core"},
    {"category": "job_search", "keyword": "爬虫", "priority": "core"},
    {"category": "job_search", "keyword": "数据采集", "priority": "core"},
    {"category": "job_search", "keyword": "自动化", "priority": "core"},
    # 招聘搜索关键词 - 扩展
    {"category": "job_search", "keyword": "RPA", "priority": "extended"},
    {"category": "job_search", "keyword": "Android", "priority": "extended"},
    {"category": "job_search", "keyword": "远程", "priority": "extended"},
    {"category": "job_search", "keyword": "AI应用", "priority": "extended"},
    {"category": "job_search", "keyword": "数据分析", "priority": "extended"},
    # 招聘排除关键词
    {"category": "job_exclude", "keyword": "销售", "priority": "core"},
    {"category": "job_exclude", "keyword": "电话", "priority": "core"},
    {"category": "job_exclude", "keyword": "996", "priority": "core"},
    {"category": "job_exclude", "keyword": "大小周", "priority": "core"},
    {"category": "job_exclude", "keyword": "抗压", "priority": "extended"},
    {"category": "job_exclude", "keyword": "沟通能力强", "priority": "extended"},
    {"category": "job_exclude", "keyword": "外包", "priority": "extended"},
    # 论坛话题关键词
    {"category": "forum_topic", "keyword": "生活体验", "priority": "core"},
    {"category": "forum_topic", "keyword": "工作机会", "priority": "core"},
    {"category": "forum_topic", "keyword": "房租", "priority": "core"},
    {"category": "forum_topic", "keyword": "定居", "priority": "core"},
    {"category": "forum_topic", "keyword": "IT互联网", "priority": "extended"},
    {"category": "forum_topic", "keyword": "程序员", "priority": "extended"},
    {"category": "forum_topic", "keyword": "气候", "priority": "extended"},
    {"category": "forum_topic", "keyword": "生活成本", "priority": "extended"},
]

# 数据源
DATA_SOURCES = [
    # 招聘网站
    {
        "name": "58同城招聘",
        "type": "job",
        "slug": "58job",
        "priority": 1,
        "config": {"base_url": "https://www.58.com"},
    },
    {
        "name": "Boss直聘",
        "type": "job",
        "slug": "boss",
        "priority": 2,
        "enabled": False,  # 反爬严格，默认禁用
        "config": {"base_url": "https://www.zhipin.com", "note": "反爬严格，建议手动导入"},
    },
    # 房产网站
    {
        "name": "58同城租房",
        "type": "rent",
        "slug": "58rent",
        "priority": 1,
        "config": {"base_url": "https://www.58.com"},
    },
    {
        "name": "安居客",
        "type": "rent",
        "slug": "anjuke",
        "priority": 2,
        "config": {"base_url": "https://www.anjuke.com"},
    },
    # 论坛
    {
        "name": "V2EX",
        "type": "forum",
        "slug": "v2ex",
        "priority": 1,
        "config": {"base_url": "https://www.v2ex.com"},
    },
    {
        "name": "百度贴吧",
        "type": "forum",
        "slug": "tieba",
        "priority": 2,
        "config": {"base_url": "https://tieba.baidu.com"},
    },
    {
        "name": "知乎",
        "type": "forum",
        "slug": "zhihu",
        "priority": 3,
        "enabled": False,  # 反爬严格
        "config": {"base_url": "https://www.zhihu.com", "note": "反爬严格，建议手动导入"},
    },
    {
        "name": "小红书",
        "type": "forum",
        "slug": "xiaohongshu",
        "priority": 4,
        "enabled": False,  # 需要 App
        "config": {"note": "需要App，建议手动导入"},
    },
    # 公开数据
    {
        "name": "Numbeo",
        "type": "public_data",
        "slug": "numbeo",
        "priority": 1,
        "config": {"base_url": "https://www.numbeo.com"},
    },
]


async def seed_cities(session):
    """Seed cities data."""
    print("Seeding cities...")
    for city_data in CITIES:
        existing = await session.execute(
            select(City).where(City.name == city_data["name"])
        )
        if existing.scalar_one_or_none():
            print(f"  City '{city_data['name']}' already exists, skipping")
            continue
        city = City(**city_data)
        session.add(city)
        print(f"  Added city: {city_data['name']}")
    await session.commit()
    print(f"Cities seeded: {len(CITIES)} total")


async def seed_keywords(session):
    """Seed keywords data."""
    print("Seeding keywords...")
    for kw_data in KEYWORDS:
        existing = await session.execute(
            select(Keyword).where(
                Keyword.category == kw_data["category"],
                Keyword.keyword == kw_data["keyword"],
            )
        )
        if existing.scalar_one_or_none():
            print(f"  Keyword '{kw_data['keyword']}' already exists, skipping")
            continue
        keyword = Keyword(**kw_data)
        session.add(keyword)
        print(f"  Added keyword: {kw_data['keyword']} ({kw_data['category']})")
    await session.commit()
    print(f"Keywords seeded: {len(KEYWORDS)} total")


async def seed_data_sources(session):
    """Seed data sources."""
    print("Seeding data sources...")
    for source_data in DATA_SOURCES:
        existing = await session.execute(
            select(DataSource).where(DataSource.slug == source_data["slug"])
        )
        if existing.scalar_one_or_none():
            print(f"  DataSource '{source_data['name']}' already exists, skipping")
            continue
        source = DataSource(**source_data)
        session.add(source)
        print(f"  Added data source: {source_data['name']}")
    await session.commit()
    print(f"Data sources seeded: {len(DATA_SOURCES)} total")


async def main():
    """Run all seed functions."""
    print("=" * 50)
    print("CityScout Database Seeding")
    print("=" * 50)

    async with async_session() as session:
        await seed_cities(session)
        print()
        await seed_keywords(session)
        print()
        await seed_data_sources(session)

    print()
    print("=" * 50)
    print("Seeding completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
