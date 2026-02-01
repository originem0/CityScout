"""免费代理池管理器.

从多个免费代理API获取代理，并进行健康检查和轮换。
注意：免费代理可用性较低，仅用于开发测试。生产环境建议使用付费代理服务。
"""
import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class Proxy:
    """代理信息."""
    host: str
    port: int
    protocol: str = "http"  # http/https/socks5
    country: str = ""
    anonymity: str = ""  # transparent/anonymous/elite
    last_checked: datetime = field(default_factory=datetime.now)
    is_alive: bool = True
    fail_count: int = 0

    @property
    def url(self) -> str:
        """返回代理URL格式."""
        return f"{self.protocol}://{self.host}:{self.port}"

    def __hash__(self):
        return hash((self.host, self.port))

    def __eq__(self, other):
        if isinstance(other, Proxy):
            return self.host == other.host and self.port == other.port
        return False


class ProxyPool:
    """免费代理池管理器."""

    # 免费代理API源列表
    PROXY_SOURCES = [
        {
            "name": "geonode",
            "url": "https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps",
            "parser": "_parse_geonode",
        },
        {
            "name": "proxyscrape",
            "url": "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            "parser": "_parse_proxyscrape",
        },
    ]

    # 用于验证代理的测试URL
    TEST_URLS = [
        "http://httpbin.org/ip",
        "https://api.ipify.org?format=json",
    ]

    def __init__(
        self,
        pool_size: int = 20,
        max_fail_count: int = 3,
        check_timeout: int = 10,
    ):
        """初始化代理池.

        Args:
            pool_size: 保持的可用代理数量
            max_fail_count: 最大失败次数，超过后移除代理
            check_timeout: 健康检查超时秒数
        """
        self.pool_size = pool_size
        self.max_fail_count = max_fail_count
        self.check_timeout = check_timeout
        self._proxies: dict[str, Proxy] = {}  # host:port -> Proxy
        self._lock = asyncio.Lock()
        self._last_fetch: datetime | None = None
        self._fetch_interval = 300  # 5分钟刷新一次代理列表

    async def fetch_proxies(self) -> list[Proxy]:
        """从多个源获取代理列表."""
        all_proxies = []

        async with httpx.AsyncClient(timeout=15) as client:
            for source in self.PROXY_SOURCES:
                try:
                    logger.debug(f"Fetching proxies from {source['name']}...")
                    response = await client.get(source["url"])
                    if response.status_code == 200:
                        parser = getattr(self, source["parser"])
                        proxies = parser(response)
                        all_proxies.extend(proxies)
                        logger.info(f"Got {len(proxies)} proxies from {source['name']}")
                except Exception as e:
                    logger.warning(f"Failed to fetch from {source['name']}: {e}")

        # 去重
        unique_proxies = list({p.url: p for p in all_proxies}.values())
        logger.info(f"Total unique proxies fetched: {len(unique_proxies)}")
        return unique_proxies

    def _parse_geonode(self, response: httpx.Response) -> list[Proxy]:
        """解析 geonode API 响应."""
        proxies = []
        try:
            data = response.json()
            for item in data.get("data", []):
                proxy = Proxy(
                    host=item.get("ip", ""),
                    port=int(item.get("port", 0)),
                    protocol=item.get("protocols", ["http"])[0].lower(),
                    country=item.get("country", ""),
                    anonymity=item.get("anonymityLevel", ""),
                )
                if proxy.host and proxy.port:
                    proxies.append(proxy)
        except Exception as e:
            logger.warning(f"Failed to parse geonode response: {e}")
        return proxies

    def _parse_proxyscrape(self, response: httpx.Response) -> list[Proxy]:
        """解析 proxyscrape API 响应 (纯文本格式: ip:port)."""
        proxies = []
        try:
            lines = response.text.strip().split("\n")
            for line in lines:
                line = line.strip()
                if ":" in line:
                    parts = line.split(":")
                    if len(parts) == 2:
                        proxy = Proxy(
                            host=parts[0],
                            port=int(parts[1]),
                            protocol="http",
                        )
                        proxies.append(proxy)
        except Exception as e:
            logger.warning(f"Failed to parse proxyscrape response: {e}")
        return proxies

    async def health_check(self, proxy: Proxy) -> bool:
        """验证代理是否可用."""
        test_url = random.choice(self.TEST_URLS)
        try:
            async with httpx.AsyncClient(
                proxies={
                    "http://": proxy.url,
                    "https://": proxy.url,
                },
                timeout=self.check_timeout,
            ) as client:
                response = await client.get(test_url)
                if response.status_code == 200:
                    proxy.is_alive = True
                    proxy.fail_count = 0
                    proxy.last_checked = datetime.now()
                    return True
        except Exception as e:
            logger.debug(f"Proxy {proxy.url} failed health check: {e}")

        proxy.is_alive = False
        proxy.fail_count += 1
        return False

    async def refresh_pool(self, force: bool = False):
        """刷新代理池.

        Args:
            force: 强制刷新，忽略时间间隔
        """
        async with self._lock:
            now = datetime.now()

            # 检查是否需要刷新
            if not force and self._last_fetch:
                elapsed = (now - self._last_fetch).total_seconds()
                if elapsed < self._fetch_interval and len(self._proxies) >= self.pool_size // 2:
                    return

            logger.info("Refreshing proxy pool...")
            self._last_fetch = now

            # 获取新代理
            new_proxies = await self.fetch_proxies()

            # 并发验证代理（限制并发数）
            semaphore = asyncio.Semaphore(10)

            async def check_with_semaphore(p: Proxy) -> tuple[Proxy, bool]:
                async with semaphore:
                    result = await self.health_check(p)
                    return p, result

            tasks = [check_with_semaphore(p) for p in new_proxies[:50]]  # 只验证前50个
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 添加可用代理
            added = 0
            for result in results:
                if isinstance(result, tuple):
                    proxy, is_alive = result
                    if is_alive:
                        key = f"{proxy.host}:{proxy.port}"
                        self._proxies[key] = proxy
                        added += 1
                        if len(self._proxies) >= self.pool_size:
                            break

            logger.info(f"Proxy pool refreshed: {added} alive, {len(self._proxies)} total")

    async def get_working_proxy(self) -> Proxy | None:
        """获取一个可用代理.

        Returns:
            可用代理或None
        """
        # 确保有足够的代理
        if len(self._proxies) < self.pool_size // 2:
            await self.refresh_pool()

        # 随机选择一个可用代理
        alive_proxies = [p for p in self._proxies.values() if p.is_alive]
        if not alive_proxies:
            logger.warning("No alive proxies available, refreshing pool...")
            await self.refresh_pool(force=True)
            alive_proxies = [p for p in self._proxies.values() if p.is_alive]

        if alive_proxies:
            return random.choice(alive_proxies)

        logger.error("No proxies available after refresh")
        return None

    async def mark_dead(self, proxy: Proxy):
        """标记代理失效."""
        async with self._lock:
            key = f"{proxy.host}:{proxy.port}"
            if key in self._proxies:
                self._proxies[key].is_alive = False
                self._proxies[key].fail_count += 1

                # 如果失败次数过多，移除代理
                if self._proxies[key].fail_count >= self.max_fail_count:
                    del self._proxies[key]
                    logger.debug(f"Removed proxy {key} after {self.max_fail_count} failures")

    async def mark_success(self, proxy: Proxy):
        """标记代理成功使用."""
        async with self._lock:
            key = f"{proxy.host}:{proxy.port}"
            if key in self._proxies:
                self._proxies[key].is_alive = True
                self._proxies[key].fail_count = 0
                self._proxies[key].last_checked = datetime.now()

    def get_stats(self) -> dict:
        """获取代理池统计信息."""
        alive = sum(1 for p in self._proxies.values() if p.is_alive)
        return {
            "total": len(self._proxies),
            "alive": alive,
            "dead": len(self._proxies) - alive,
            "last_fetch": self._last_fetch.isoformat() if self._last_fetch else None,
        }


# 全局单例
_proxy_pool: ProxyPool | None = None


def get_proxy_pool(
    pool_size: int = 20,
    max_fail_count: int = 3,
    check_timeout: int = 10,
) -> ProxyPool:
    """获取代理池单例."""
    global _proxy_pool
    if _proxy_pool is None:
        _proxy_pool = ProxyPool(
            pool_size=pool_size,
            max_fail_count=max_fail_count,
            check_timeout=check_timeout,
        )
    return _proxy_pool
