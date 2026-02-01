"""爬虫共享常量.

将各爬虫中重复定义的常量提取到公共文件。
"""

# 58同城城市代码映射
CITY_CODES_58 = {
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

# 58同城分页选择器
PAGINATION_SELECTORS_58 = [
    "a.next",
    ".pager a.next",
    "a[class*='next']",
    "a:has-text('下一页')",
]

# 58同城职位列表选择器（按优先级排列）
JOB_LIST_SELECTORS = [
    ".job_list li",
    ".list-item",
    "[class*='job'] li",
]

# 58同城租房列表选择器（按优先级排列）
RENT_LIST_SELECTORS = [
    ".house-list li",
    ".list-item",
    "[class*='house'] li",
    ".property-list li",
]

# 看准网配置
KANZHUN_CONFIG = {
    "base_url": "https://www.kanzhun.com",
    "search_url": "https://www.kanzhun.com/search/",
    "rate_limit": 0.3,  # 每3秒1请求
    "selectors": {
        "company_item": ".company-item, .search-result-item",
        "company_link": ".company-item a, a[href*='/gsr'], a[href*='/company']",
        "overall_rating": ".company-score .score-num, .overall-score, .score-value",
        "review_count": ".review-count, .comment-count",
        "recommend_rate": ".recommend-rate, .recommend",
        "company_name": ".company-name, .name, h1",
        "company_intro": ".company-intro, .company-summary, .intro",
        "industry": ".company-industry, .industry, .tag-industry",
    },
    "rating_dimensions": {
        "culture_rating": ".culture-score, [data-type='culture'] .score",
        "management_rating": ".management-score, [data-type='management'] .score",
        "salary_benefit_rating": ".salary-score, [data-type='salary'] .score",
        "career_rating": ".career-score, [data-type='career'] .score",
        "work_life_balance": ".balance-score, [data-type='balance'] .score",
    },
}

# 职友集配置
ZHIYOUJI_CONFIG = {
    "base_url": "https://www.jobui.com",
    "search_url": "https://www.jobui.com/search.php",
    "rate_limit": 0.5,  # 每2秒1请求
    "selectors": {
        "company_item": ".company-item, .search-company",
        "company_link": ".company-name a, .company-item a, a[href*='/company/']",
        "avg_salary": ".avg-salary, .average-salary, .salary-avg, .salary-value",
        "sample_count": ".sample-count, .salary-count, .data-count",
        "distribution_bar": ".distribution-item, .salary-bar, .chart-item",
    },
}

# 数据源类型映射
DATA_SOURCE_TYPES = {
    "job": ["58同城", "智联招聘", "前程无忧", "Boss直聘"],
    "rent": ["58同城", "链家", "贝壳", "安居客"],
    "forum": ["小红书", "知乎", "豆瓣", "虎扑"],
    "company_review": ["看准网"],
    "salary_stats": ["职友集"],
    "public_data": ["统计局", "住建部"],
}
