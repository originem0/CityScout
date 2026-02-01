"""职位描述（JD）技能词提取服务.

从职位描述中提取技术技能关键词，用于技能趋势分析。
"""
import re
from collections import Counter
from typing import Optional


# 技术技能关键词库
TECH_KEYWORDS = {
    "languages": [
        "Python", "Java", "JavaScript", "TypeScript", "Go", "Golang", "Rust",
        "C++", "C#", "PHP", "Ruby", "Swift", "Kotlin", "Scala", "R",
        "Perl", "Lua", "Shell", "Bash", "SQL", "HTML", "CSS", "SASS", "Less",
    ],
    "frontend": [
        "React", "Vue", "Angular", "Next.js", "Nuxt", "Svelte", "jQuery",
        "Webpack", "Vite", "Rollup", "Babel", "ESLint", "Prettier",
        "Tailwind", "Bootstrap", "Ant Design", "Element UI", "Material UI",
        "Redux", "Vuex", "Pinia", "MobX", "Zustand",
        "uni-app", "小程序", "微信小程序", "React Native", "Flutter",
    ],
    "backend": [
        "Spring", "Spring Boot", "Django", "Flask", "FastAPI", "Express",
        "Nest.js", "Koa", "Gin", "Echo", "Fiber", "Laravel", "Rails",
        "ASP.NET", "Node.js", "Deno", "GraphQL", "REST", "gRPC",
        "微服务", "Microservices", "Serverless",
    ],
    "databases": [
        "MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
        "Oracle", "SQL Server", "SQLite", "MariaDB", "TiDB",
        "Cassandra", "HBase", "ClickHouse", "Neo4j", "InfluxDB",
        "Memcached", "DynamoDB", "CouchDB",
    ],
    "devops": [
        "Docker", "Kubernetes", "K8s", "Jenkins", "GitLab CI", "GitHub Actions",
        "Terraform", "Ansible", "Puppet", "Chef", "Prometheus", "Grafana",
        "ELK", "Nginx", "Apache", "Tomcat", "AWS", "Azure", "GCP", "阿里云",
        "腾讯云", "华为云", "Linux", "Unix", "CI/CD",
    ],
    "ai_ml": [
        "机器学习", "深度学习", "人工智能", "AI", "ML", "NLP", "自然语言处理",
        "计算机视觉", "CV", "TensorFlow", "PyTorch", "Keras", "Scikit-learn",
        "Pandas", "NumPy", "OpenCV", "BERT", "GPT", "LLM", "大模型",
        "推荐系统", "数据挖掘", "神经网络",
    ],
    "bigdata": [
        "大数据", "Hadoop", "Spark", "Flink", "Kafka", "Hive", "Presto",
        "Airflow", "ETL", "数据仓库", "数据湖", "OLAP", "实时计算",
        "Storm", "Beam", "Druid", "Kylin",
    ],
    "mobile": [
        "iOS", "Android", "Swift", "Objective-C", "Kotlin", "Java",
        "React Native", "Flutter", "Dart", "Xamarin", "Cordova",
        "移动端", "App开发", "原生开发", "跨平台",
    ],
    "tools": [
        "Git", "SVN", "Jira", "Confluence", "Trello", "Notion",
        "VS Code", "IntelliJ", "Eclipse", "Vim", "Postman", "Swagger",
        "Maven", "Gradle", "npm", "yarn", "pnpm", "pip",
    ],
}

# 扁平化关键词列表用于快速查找
ALL_KEYWORDS: set[str] = set()
KEYWORD_CATEGORY: dict[str, str] = {}

for category, keywords in TECH_KEYWORDS.items():
    for kw in keywords:
        ALL_KEYWORDS.add(kw.lower())
        KEYWORD_CATEGORY[kw.lower()] = category


def extract_skills(description: str) -> dict[str, list[str]]:
    """从职位描述中提取技能关键词.

    Args:
        description: 职位描述文本

    Returns:
        按类别分组的技能列表
    """
    if not description:
        return {}

    found_skills: dict[str, set[str]] = {cat: set() for cat in TECH_KEYWORDS}

    # 预处理文本
    text = description.lower()

    # 匹配每个关键词
    for category, keywords in TECH_KEYWORDS.items():
        for keyword in keywords:
            # 使用单词边界匹配，避免误匹配
            # 对于中文关键词直接包含匹配
            kw_lower = keyword.lower()
            if re.search(rf"\b{re.escape(kw_lower)}\b", text) or keyword in description:
                found_skills[category].add(keyword)

    # 转换为列表并排序
    result = {}
    for cat, skills in found_skills.items():
        if skills:
            result[cat] = sorted(skills)

    return result


def extract_skills_flat(description: str) -> list[str]:
    """从职位描述中提取技能关键词（扁平列表）.

    Args:
        description: 职位描述文本

    Returns:
        技能关键词列表
    """
    skills_by_category = extract_skills(description)
    all_skills = []
    for skills in skills_by_category.values():
        all_skills.extend(skills)
    return sorted(set(all_skills))


def analyze_skill_trends(descriptions: list[str]) -> dict:
    """分析多个职位描述的技能趋势.

    Args:
        descriptions: 职位描述列表

    Returns:
        技能统计信息
    """
    skill_counter: Counter[str] = Counter()
    category_counter: Counter[str] = Counter()
    total_jobs = len(descriptions)

    for desc in descriptions:
        if not desc:
            continue
        skills = extract_skills_flat(desc)
        for skill in skills:
            skill_counter[skill] += 1
            category = KEYWORD_CATEGORY.get(skill.lower(), "other")
            category_counter[category] += 1

    # 计算出现率
    skill_stats = []
    for skill, count in skill_counter.most_common():
        skill_stats.append({
            "skill": skill,
            "count": count,
            "percentage": round(count / total_jobs * 100, 1) if total_jobs > 0 else 0,
            "category": KEYWORD_CATEGORY.get(skill.lower(), "other"),
        })

    category_stats = []
    for cat, count in category_counter.most_common():
        category_stats.append({
            "category": cat,
            "count": count,
            "percentage": round(count / total_jobs * 100, 1) if total_jobs > 0 else 0,
        })

    return {
        "total_jobs_analyzed": total_jobs,
        "unique_skills_found": len(skill_counter),
        "top_skills": skill_stats[:30],
        "category_distribution": category_stats,
    }
