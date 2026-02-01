"""City analysis API endpoints."""
from fastapi import APIRouter, Query
from sqlalchemy import select, func, case, distinct
from sqlalchemy.orm import joinedload

from app.api.deps import DbSession
from app.models import Job, Rent, ForumPost, City, CityStats

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/city-comparison")
async def city_comparison(
    db: DbSession,
    city_ids: str | None = Query(None, description="Comma-separated city IDs"),
):
    """Get comprehensive comparison data for cities."""
    # Filter cities
    city_filter = []
    if city_ids:
        city_filter = [int(x) for x in city_ids.split(",") if x.strip()]

    # Get all enabled cities if no filter
    if city_filter:
        city_query = select(City).where(City.id.in_(city_filter))
    else:
        city_query = select(City).where(City.enabled == True)

    cities_result = await db.execute(city_query)
    cities = cities_result.scalars().all()
    city_id_list = [c.id for c in cities]

    if not city_id_list:
        return {"cities": [], "comparison": []}

    # Job stats per city
    job_stats_query = (
        select(
            Job.city_id,
            func.count(Job.id).label("job_count"),
            func.avg(Job.salary_min).label("avg_salary_min"),
            func.avg(Job.salary_max).label("avg_salary_max"),
            func.min(Job.salary_min).label("min_salary"),
            func.max(Job.salary_max).label("max_salary"),
            func.avg((Job.salary_min + Job.salary_max) / 2).label("avg_salary"),
        )
        .where(Job.city_id.in_(city_id_list))
        .group_by(Job.city_id)
    )
    job_result = await db.execute(job_stats_query)
    job_stats = {r.city_id: r for r in job_result.all()}

    # Rent stats per city
    rent_stats_query = (
        select(
            Rent.city_id,
            func.count(Rent.id).label("rent_count"),
            func.avg(Rent.price).label("avg_rent"),
            func.min(Rent.price).label("min_rent"),
            func.max(Rent.price).label("max_rent"),
            func.avg(Rent.area).label("avg_area"),
        )
        .where(Rent.city_id.in_(city_id_list))
        .group_by(Rent.city_id)
    )
    rent_result = await db.execute(rent_stats_query)
    rent_stats = {r.city_id: r for r in rent_result.all()}

    # Forum stats per city
    forum_stats_query = (
        select(
            ForumPost.city_id,
            func.count(ForumPost.id).label("post_count"),
            func.sum(ForumPost.likes).label("total_likes"),
            func.sum(ForumPost.replies_count).label("total_replies"),
        )
        .where(ForumPost.city_id.in_(city_id_list))
        .group_by(ForumPost.city_id)
    )
    forum_result = await db.execute(forum_stats_query)
    forum_stats = {r.city_id: r for r in forum_result.all()}

    # City stats (公开统计数据)
    city_stats_query = (
        select(CityStats)
        .where(CityStats.city_id.in_(city_id_list))
    )
    city_stats_result = await db.execute(city_stats_query)
    city_stats = {r.city_id: r for r in city_stats_result.scalars().all()}

    # Build comparison data
    comparison = []
    for city in cities:
        js = job_stats.get(city.id)
        rs = rent_stats.get(city.id)
        fs = forum_stats.get(city.id)
        cs = city_stats.get(city.id)

        avg_salary = float(js.avg_salary) if js and js.avg_salary else None
        avg_rent = float(rs.avg_rent) if rs and rs.avg_rent else None

        # Salary-to-rent ratio
        salary_rent_ratio = None
        if avg_salary and avg_rent and avg_rent > 0:
            salary_rent_ratio = round(avg_salary / avg_rent, 1)

        comparison.append({
            "city_id": city.id,
            "city_name": city.name,
            "province": city.province,
            "tier": city.tier,
            # 爬取的职位数据
            "job_count": js.job_count if js else 0,
            "avg_salary_min": round(float(js.avg_salary_min), 0) if js and js.avg_salary_min else None,
            "avg_salary_max": round(float(js.avg_salary_max), 0) if js and js.avg_salary_max else None,
            "avg_salary": round(avg_salary, 0) if avg_salary else None,
            # 爬取的租房数据
            "rent_count": rs.rent_count if rs else 0,
            "avg_rent": round(avg_rent, 0) if avg_rent else None,
            "min_rent": round(float(rs.min_rent), 0) if rs and rs.min_rent else None,
            "max_rent": round(float(rs.max_rent), 0) if rs and rs.max_rent else None,
            "avg_area": round(float(rs.avg_area), 1) if rs and rs.avg_area else None,
            # 论坛数据
            "post_count": fs.post_count if fs else 0,
            "total_likes": fs.total_likes if fs else 0,
            "total_replies": fs.total_replies if fs else 0,
            # 计算指标
            "salary_rent_ratio": salary_rent_ratio,
            # 公开统计数据 (city_stats)
            "population": float(cs.population) if cs and cs.population else None,
            "gdp": float(cs.gdp) if cs and cs.gdp else None,
            "gdp_per_capita": float(cs.gdp_per_capita) if cs and cs.gdp_per_capita else None,
            "official_avg_salary": float(cs.avg_salary) if cs and cs.avg_salary else None,
            "living_cost_index": float(cs.living_cost_index) if cs and cs.living_cost_index else None,
            "housing_price": float(cs.housing_price) if cs and cs.housing_price else None,
            "avg_temp_year": float(cs.avg_temp_year) if cs and cs.avg_temp_year else None,
            "avg_temp_summer": float(cs.avg_temp_summer) if cs and cs.avg_temp_summer else None,
            "avg_temp_winter": float(cs.avg_temp_winter) if cs and cs.avg_temp_winter else None,
            "air_quality_index": cs.air_quality_index if cs else None,
            "sunny_days": cs.sunny_days if cs else None,
        })

    return {
        "cities": [{"id": c.id, "name": c.name, "province": c.province, "tier": c.tier} for c in cities],
        "comparison": comparison,
    }


@router.get("/rankings")
async def city_rankings(
    db: DbSession,
    dimension: str = Query("salary", description="salary|rent|ratio|jobs|forum"),
    limit: int = Query(20, ge=1, le=50),
):
    """Get city rankings by dimension."""
    if dimension == "salary":
        query = (
            select(
                Job.city_id,
                City.name.label("city_name"),
                City.province,
                func.avg((Job.salary_min + Job.salary_max) / 2).label("value"),
                func.count(Job.id).label("sample_size"),
            )
            .join(City, Job.city_id == City.id)
            .group_by(Job.city_id, City.name, City.province)
            .having(func.count(Job.id) >= 1)
            .order_by(func.avg((Job.salary_min + Job.salary_max) / 2).desc())
            .limit(limit)
        )
        label = "平均薪资"
        unit = "元/月"

    elif dimension == "rent":
        query = (
            select(
                Rent.city_id,
                City.name.label("city_name"),
                City.province,
                func.avg(Rent.price).label("value"),
                func.count(Rent.id).label("sample_size"),
            )
            .join(City, Rent.city_id == City.id)
            .group_by(Rent.city_id, City.name, City.province)
            .having(func.count(Rent.id) >= 1)
            .order_by(func.avg(Rent.price).asc())
            .limit(limit)
        )
        label = "平均房租"
        unit = "元/月"

    elif dimension == "ratio":
        # Salary-to-rent ratio (higher is better)
        salary_sub = (
            select(
                Job.city_id,
                func.avg((Job.salary_min + Job.salary_max) / 2).label("avg_salary"),
            )
            .group_by(Job.city_id)
            .subquery()
        )
        rent_sub = (
            select(
                Rent.city_id,
                func.avg(Rent.price).label("avg_rent"),
            )
            .group_by(Rent.city_id)
            .subquery()
        )
        query = (
            select(
                City.id.label("city_id"),
                City.name.label("city_name"),
                City.province,
                (salary_sub.c.avg_salary / rent_sub.c.avg_rent).label("value"),
            )
            .join(salary_sub, City.id == salary_sub.c.city_id)
            .join(rent_sub, City.id == rent_sub.c.city_id)
            .where(rent_sub.c.avg_rent > 0)
            .order_by((salary_sub.c.avg_salary / rent_sub.c.avg_rent).desc())
            .limit(limit)
        )
        label = "薪租比"
        unit = "倍"

    elif dimension == "jobs":
        query = (
            select(
                Job.city_id,
                City.name.label("city_name"),
                City.province,
                func.count(Job.id).label("value"),
            )
            .join(City, Job.city_id == City.id)
            .group_by(Job.city_id, City.name, City.province)
            .order_by(func.count(Job.id).desc())
            .limit(limit)
        )
        label = "岗位数量"
        unit = "个"

    elif dimension == "forum":
        query = (
            select(
                ForumPost.city_id,
                City.name.label("city_name"),
                City.province,
                func.count(ForumPost.id).label("value"),
            )
            .join(City, ForumPost.city_id == City.id)
            .where(ForumPost.city_id.isnot(None))
            .group_by(ForumPost.city_id, City.name, City.province)
            .order_by(func.count(ForumPost.id).desc())
            .limit(limit)
        )
        label = "讨论热度"
        unit = "帖"

    else:
        return {"error": "Invalid dimension"}

    result = await db.execute(query)
    rows = result.all()

    rankings = []
    for i, row in enumerate(rows, 1):
        entry = {
            "rank": i,
            "city_id": row.city_id,
            "city_name": row.city_name,
            "province": row.province,
            "value": round(float(row.value), 1) if row.value else 0,
        }
        if hasattr(row, "sample_size"):
            entry["sample_size"] = row.sample_size
        rankings.append(entry)

    return {
        "dimension": dimension,
        "label": label,
        "unit": unit,
        "rankings": rankings,
    }


@router.get("/score")
async def city_scores(
    db: DbSession,
    weights: str | None = Query(
        None, description="salary:40,rent:30,ratio:20,forum:10"
    ),
):
    """Calculate composite scores for cities."""
    # Parse weights
    w = {"salary": 40, "rent": 30, "ratio": 20, "forum": 10}
    if weights:
        for part in weights.split(","):
            k, v = part.split(":")
            w[k.strip()] = int(v.strip())

    total_weight = sum(w.values())

    # Get all enabled cities
    cities_result = await db.execute(
        select(City).where(City.enabled == True)
    )
    cities = cities_result.scalars().all()
    city_ids = [c.id for c in cities]

    if not city_ids:
        return {"weights": w, "scores": []}

    # Gather raw data per city
    # Salary averages
    salary_q = (
        select(
            Job.city_id,
            func.avg((Job.salary_min + Job.salary_max) / 2).label("avg_salary"),
        )
        .where(Job.city_id.in_(city_ids))
        .group_by(Job.city_id)
    )
    salary_result = await db.execute(salary_q)
    salary_data = {r.city_id: float(r.avg_salary) for r in salary_result.all() if r.avg_salary}

    # Rent averages
    rent_q = (
        select(
            Rent.city_id,
            func.avg(Rent.price).label("avg_rent"),
        )
        .where(Rent.city_id.in_(city_ids))
        .group_by(Rent.city_id)
    )
    rent_result = await db.execute(rent_q)
    rent_data = {r.city_id: float(r.avg_rent) for r in rent_result.all() if r.avg_rent}

    # Forum counts
    forum_q = (
        select(
            ForumPost.city_id,
            func.count(ForumPost.id).label("post_count"),
        )
        .where(ForumPost.city_id.in_(city_ids))
        .group_by(ForumPost.city_id)
    )
    forum_result = await db.execute(forum_q)
    forum_data = {r.city_id: r.post_count for r in forum_result.all()}

    # Normalize and score
    def normalize(values: dict, higher_better: bool = True) -> dict:
        """Normalize values to 0-100 scale."""
        if not values:
            return {}
        vals = list(values.values())
        min_v, max_v = min(vals), max(vals)
        if max_v == min_v:
            return {k: 50.0 for k in values}
        result = {}
        for k, v in values.items():
            if higher_better:
                result[k] = ((v - min_v) / (max_v - min_v)) * 100
            else:
                result[k] = ((max_v - v) / (max_v - min_v)) * 100
        return result

    salary_norm = normalize(salary_data, higher_better=True)
    rent_norm = normalize(rent_data, higher_better=False)  # Lower rent is better

    # Salary-to-rent ratio
    ratio_data = {}
    for cid in city_ids:
        if cid in salary_data and cid in rent_data and rent_data[cid] > 0:
            ratio_data[cid] = salary_data[cid] / rent_data[cid]
    ratio_norm = normalize(ratio_data, higher_better=True)

    forum_norm = normalize(forum_data, higher_better=True)

    # Calculate composite score
    scores = []
    for city in cities:
        cid = city.id
        s_score = salary_norm.get(cid, 0)
        r_score = rent_norm.get(cid, 0)
        ratio_score = ratio_norm.get(cid, 0)
        f_score = forum_norm.get(cid, 0)

        composite = (
            s_score * w["salary"]
            + r_score * w["rent"]
            + ratio_score * w["ratio"]
            + f_score * w["forum"]
        ) / total_weight

        scores.append({
            "city_id": cid,
            "city_name": city.name,
            "province": city.province,
            "tier": city.tier,
            "composite_score": round(composite, 1),
            "salary_score": round(s_score, 1),
            "rent_score": round(r_score, 1),
            "ratio_score": round(ratio_score, 1),
            "forum_score": round(f_score, 1),
            "avg_salary": round(salary_data.get(cid, 0), 0) if cid in salary_data else None,
            "avg_rent": round(rent_data.get(cid, 0), 0) if cid in rent_data else None,
            "salary_rent_ratio": round(ratio_data.get(cid, 0), 1) if cid in ratio_data else None,
            "post_count": forum_data.get(cid, 0),
        })

    scores.sort(key=lambda x: x["composite_score"], reverse=True)

    # Add rank
    for i, s in enumerate(scores, 1):
        s["rank"] = i

    return {
        "weights": w,
        "scores": scores,
    }


@router.get("/skills-trend")
async def skills_trend(
    db: DbSession,
    city_id: int | None = Query(None, description="Filter by city ID"),
    limit: int = Query(30, ge=1, le=100, description="Number of top skills to return"),
):
    """Analyze skill keyword trends from job descriptions.

    Extracts technical skills from job descriptions and returns
    frequency rankings by skill and category.
    """
    from app.services.jd_parser import analyze_skill_trends

    # Build query for job descriptions
    query = select(Job.description).where(Job.description.isnot(None))
    if city_id:
        query = query.where(Job.city_id == city_id)

    result = await db.execute(query)
    descriptions = [row[0] for row in result.all() if row[0]]

    if not descriptions:
        return {
            "total_jobs_analyzed": 0,
            "unique_skills_found": 0,
            "top_skills": [],
            "category_distribution": [],
            "city_id": city_id,
        }

    # Analyze skills
    trend_data = analyze_skill_trends(descriptions)
    trend_data["city_id"] = city_id

    # Limit top skills
    if len(trend_data["top_skills"]) > limit:
        trend_data["top_skills"] = trend_data["top_skills"][:limit]

    return trend_data

