"""System settings API endpoints."""
import json
from pathlib import Path
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/settings", tags=["settings"])

# Settings file path
SETTINGS_FILE = Path(__file__).parent.parent.parent / "settings.json"

# Default settings
DEFAULT_SETTINGS = {
    "crawler": {
        "request_interval": 2.0,  # seconds between requests
        "page_timeout": 30000,  # ms
        "max_retries": 3,
        "max_pages": 10,  # max pages per task
        "user_agent_rotation": True,
    },
    "proxy": {
        "enabled": False,
        "list": [],  # list of proxy URLs
        "rotation": True,
    },
}


class CrawlerSettings(BaseModel):
    request_interval: float = 2.0
    page_timeout: int = 30000
    max_retries: int = 3
    max_pages: int = 10
    user_agent_rotation: bool = True


class ProxySettings(BaseModel):
    enabled: bool = False
    proxy_list: List[str] = Field(default=[], alias="list")
    rotation: bool = True

    model_config = {"populate_by_name": True}


class SystemSettings(BaseModel):
    crawler: CrawlerSettings = CrawlerSettings()
    proxy: ProxySettings = ProxySettings()


def load_settings() -> dict:
    """Load settings from file."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                # Merge with defaults
                settings = DEFAULT_SETTINGS.copy()
                settings["crawler"].update(saved.get("crawler", {}))
                settings["proxy"].update(saved.get("proxy", {}))
                return settings
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> None:
    """Save settings to file."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


@router.get("", response_model=SystemSettings)
async def get_settings():
    """Get current system settings."""
    return load_settings()


@router.put("", response_model=SystemSettings)
async def update_settings(settings: SystemSettings):
    """Update system settings."""
    data = settings.model_dump(by_alias=True)
    save_settings(data)
    return data


@router.get("/crawler", response_model=CrawlerSettings)
async def get_crawler_settings():
    """Get crawler settings."""
    settings = load_settings()
    return settings["crawler"]


@router.put("/crawler", response_model=CrawlerSettings)
async def update_crawler_settings(crawler: CrawlerSettings):
    """Update crawler settings."""
    settings = load_settings()
    settings["crawler"] = crawler.model_dump()
    save_settings(settings)
    return settings["crawler"]


@router.get("/proxy", response_model=ProxySettings)
async def get_proxy_settings():
    """Get proxy settings."""
    settings = load_settings()
    return settings["proxy"]


@router.put("/proxy", response_model=ProxySettings)
async def update_proxy_settings(proxy: ProxySettings):
    """Update proxy settings."""
    settings = load_settings()
    settings["proxy"] = proxy.model_dump(by_alias=True)
    save_settings(settings)
    return settings["proxy"]


@router.post("/proxy/test")
async def test_proxy(proxy_url: str):
    """Test a proxy connection."""
    import httpx

    try:
        async with httpx.AsyncClient(proxy=proxy_url, timeout=10) as client:
            response = await client.get("https://httpbin.org/ip")
            if response.status_code == 200:
                return {"success": True, "ip": response.json().get("origin")}
    except Exception as e:
        return {"success": False, "error": str(e)}

    return {"success": False, "error": "Unknown error"}
