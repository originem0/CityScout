"""City statistics model for public data."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CityStats(Base):
    """City statistics and public data."""

    __tablename__ = "city_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    city_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cities.id"), nullable=False
    )
    data_source_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("data_sources.id"), nullable=True
    )

    # Population and economy
    population: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 万人
    gdp: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)  # 亿元
    gdp_per_capita: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )  # 元
    avg_salary: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )  # 月均工资

    # Living costs
    living_cost_index: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )  # 生活成本指数 (100 = baseline)
    housing_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )  # 平均房价 元/㎡

    # Climate
    avg_temp_year: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 1), nullable=True
    )  # 年均温度 ℃
    avg_temp_summer: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 1), nullable=True
    )  # 夏季均温 ℃
    avg_temp_winter: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 1), nullable=True
    )  # 冬季均温 ℃
    rainfall: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 年降水量 mm
    sunny_days: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 年晴天数
    air_quality_index: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # 空气质量指数

    # Other info
    area: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )  # 面积 km²
    description: Mapped[str | None] = mapped_column(Text, nullable=True)  # 城市简介

    # Data year/source
    data_year: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 数据年份
    source_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    city = relationship("City", lazy="joined")
    data_source = relationship("DataSource", lazy="joined")
