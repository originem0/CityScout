from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "CityScout"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/cityscout"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Crawler defaults
    CRAWLER_RATE_LIMIT: float = 1.0  # requests per second
    CRAWLER_RETRY_MAX: int = 3
    CRAWLER_TIMEOUT: int = 30
    CRAWLER_MAX_PAGES: int = 5  # 默认爬取页数

    # Proxy settings
    PROXY_ENABLED: bool = True  # 是否启用代理池
    PROXY_POOL_SIZE: int = 20  # 保持的可用代理数量
    PROXY_CHECK_TIMEOUT: int = 10  # 代理健康检查超时秒数
    PROXY_MAX_FAIL_COUNT: int = 3  # 代理最大失败次数

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
