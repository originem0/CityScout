"""V2EX and general forum crawler implementation."""
import logging
import re
from datetime import datetime
from typing import Callable, Awaitable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.crawlers.base import BaseCrawler
from app.models import ForumPost, City, DataSource, Keyword

logger = logging.getLogger(__name__)


class ForumCrawler(BaseCrawler):
    """Crawler for forum posts (V2EX, etc.)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.db_session_factory = None
        self.posts_collected = []

    async def _init_db(self):
        """Initialize database connection."""
        engine = create_async_engine(settings.DATABASE_URL)
        self.db_session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

    async def _get_city_name(self, db: AsyncSession) -> str | None:
        """Get city name for search."""
        if not self.city_id:
            return None

        result = await db.execute(select(City).where(City.id == self.city_id))
        city = result.scalar_one_or_none()
        return city.name if city else None

    async def _get_data_source(self, db: AsyncSession) -> DataSource | None:
        """Get data source info."""
        if not self.data_source_id:
            return None

        result = await db.execute(
            select(DataSource).where(DataSource.id == self.data_source_id)
        )
        return result.scalar_one_or_none()

    async def _get_search_keywords(self, db: AsyncSession) -> list[str]:
        """Get forum topic keywords for search."""
        result = await db.execute(
            select(Keyword).where(
                Keyword.category == "forum_topic",
                Keyword.enabled == True,
            )
        )
        keywords = result.scalars().all()
        return [k.keyword for k in keywords]

    async def crawl(
        self,
        on_progress: Callable[[int, int], Awaitable[None]] | None = None,
    ) -> dict:
        """Crawl forum posts.

        Args:
            on_progress: Callback for progress updates (progress%, record_count)

        Returns:
            dict with crawl results including records_count
        """
        await self._init_db()

        async with self.db_session_factory() as db:
            # Get city name
            city_name = await self._get_city_name(db)

            # Get data source
            data_source = await self._get_data_source(db)
            if not data_source:
                raise ValueError(f"Data source not found: {self.data_source_id}")

            source_slug = data_source.slug

            # Get search keywords
            search_keywords = await self._get_search_keywords(db)
            if not search_keywords and city_name:
                # Use city name as default search keyword
                search_keywords = [city_name]

            logger.info(
                f"Starting forum crawl for {source_slug}, "
                f"city={city_name}, keywords={search_keywords}"
            )

            all_posts = []

            # Route to appropriate crawler
            if source_slug == "v2ex":
                all_posts = await self._crawl_v2ex(city_name, search_keywords)
            elif source_slug == "tieba":
                all_posts = await self._crawl_tieba(city_name, search_keywords)
            else:
                logger.warning(f"Unknown forum source: {source_slug}")
                return {"records_count": 0}

            if on_progress:
                await on_progress(50, len(all_posts))

            # Save to database
            saved_count = await self._save_posts(db, all_posts, city_name)

            if on_progress:
                await on_progress(100, saved_count)

            return {
                "records_count": saved_count,
                "source": source_slug,
                "city": city_name,
                "total_found": len(all_posts),
            }

    async def _crawl_v2ex(
        self, city_name: str | None, keywords: list[str]
    ) -> list[dict]:
        """Crawl V2EX forum posts."""
        all_posts = []

        for keyword in keywords[:3]:  # Limit to 3 keywords
            search_term = f"{city_name} {keyword}" if city_name else keyword
            logger.info(f"Searching V2EX for: {search_term}")

            # Use SOV2EX search (V2EX search engine)
            import urllib.parse
            encoded_term = urllib.parse.quote(search_term)
            url = f"https://www.sov2ex.com/?q={encoded_term}"

            success = await self.goto_with_retry(url)
            if not success:
                logger.warning(f"Failed to load SOV2EX search: {url}")
                continue

            # Wait for results
            await self.wait_for_selector_safe(".search-result, .result-item", timeout=10000)
            await self.wait_random(1, 2)

            # Parse search results
            posts = await self._parse_v2ex_search_results(search_term)
            all_posts.extend(posts)

            # Rate limit between searches
            await self.wait_random(2, 4)

        return all_posts

    async def _parse_v2ex_search_results(self, search_keyword: str) -> list[dict]:
        """Parse V2EX search results from SOV2EX."""
        posts = []

        # Try different selectors
        selectors = [
            ".search-result",
            ".result-item",
            "[class*='result']",
            "article",
        ]

        items = []
        for selector in selectors:
            items = await self.page.query_selector_all(selector)
            if items:
                logger.info(f"Found {len(items)} V2EX items with selector: {selector}")
                break

        if not items:
            logger.warning("No V2EX search results found")
            return posts

        for item in items[:20]:  # Limit to 20 per search
            try:
                post_data = await self._parse_v2ex_item(item, search_keyword)
                if post_data:
                    posts.append(post_data)
            except Exception as e:
                logger.warning(f"Failed to parse V2EX item: {e}")
                continue

        logger.info(f"Parsed {len(posts)} V2EX posts")
        return posts

    async def _parse_v2ex_item(self, item, search_keyword: str) -> dict | None:
        """Parse a single V2EX search result."""
        try:
            # Extract title and link
            title_el = await item.query_selector("a.topic-link, a[href*='v2ex.com/t/'], h3 a, .title a")
            if not title_el:
                return None

            title = await title_el.text_content()
            title = title.strip() if title else ""
            if not title:
                return None

            href = await title_el.get_attribute("href")
            source_url = href

            # Extract source_id from URL
            source_id = ""
            if source_url:
                match = re.search(r"/t/(\d+)", source_url)
                if match:
                    source_id = f"v2ex_{match.group(1)}"

            if not source_id:
                source_id = f"v2ex_{hash(title)}"

            # Extract content/snippet
            content_el = await item.query_selector(".content, .snippet, .desc, p")
            content = ""
            if content_el:
                content = await content_el.text_content()
                content = content.strip() if content else ""

            if not content:
                content = title  # Use title as content if no snippet

            # Extract author
            author_el = await item.query_selector(".author, .username, [class*='author']")
            author = ""
            if author_el:
                author = await author_el.text_content()
                author = author.strip() if author else ""

            # Extract node/topic
            node_el = await item.query_selector(".node, .tag, [class*='node']")
            topic = ""
            if node_el:
                topic = await node_el.text_content()
                topic = topic.strip() if topic else ""

            # Extract replies count
            replies_el = await item.query_selector(".replies, .count, [class*='replies']")
            replies_count = 0
            if replies_el:
                replies_text = await replies_el.text_content()
                if replies_text:
                    match = re.search(r"(\d+)", replies_text)
                    if match:
                        replies_count = int(match.group(1))

            # Extract time
            time_el = await item.query_selector(".time, .date, time, [class*='time']")
            posted_at = None
            if time_el:
                time_text = await time_el.text_content()
                # Parse relative time would be complex, leave as None for now

            return {
                "source_id": source_id,
                "source_url": source_url,
                "title": title,
                "content": content,
                "author": author,
                "topic": topic or "V2EX",
                "replies_count": replies_count,
                "post_type": "post",
                "search_keyword": search_keyword,
                "posted_at": posted_at,
            }

        except Exception as e:
            logger.warning(f"Error parsing V2EX item: {e}")
            return None

    async def _crawl_tieba(
        self, city_name: str | None, keywords: list[str]
    ) -> list[dict]:
        """Crawl Tieba (百度贴吧) posts."""
        all_posts = []

        # Build search terms
        search_terms = []
        if city_name:
            search_terms.append(city_name)
            for keyword in keywords[:2]:
                search_terms.append(f"{city_name} {keyword}")
        else:
            search_terms = keywords[:3]

        for search_term in search_terms:
            logger.info(f"Searching Tieba for: {search_term}")

            import urllib.parse
            encoded_term = urllib.parse.quote(search_term)
            # Tieba search URL
            url = f"https://tieba.baidu.com/f/search/res?qw={encoded_term}"

            success = await self.goto_with_retry(url)
            if not success:
                logger.warning(f"Failed to load Tieba search: {url}")
                continue

            # Wait for results
            await self.wait_for_selector_safe(".s_post, .search-item", timeout=10000)
            await self.wait_random(1, 2)

            # Parse search results
            posts = await self._parse_tieba_search_results(search_term)
            all_posts.extend(posts)

            # Rate limit between searches
            await self.wait_random(2, 4)

        return all_posts

    async def _parse_tieba_search_results(self, search_keyword: str) -> list[dict]:
        """Parse Tieba search results."""
        posts = []

        # Tieba search result selectors
        selectors = [
            ".s_post",
            ".search-item",
            ".post-item",
        ]

        items = []
        for selector in selectors:
            items = await self.page.query_selector_all(selector)
            if items:
                logger.info(f"Found {len(items)} Tieba items with selector: {selector}")
                break

        if not items:
            logger.warning("No Tieba search results found")
            return posts

        for item in items[:20]:  # Limit to 20 per search
            try:
                post_data = await self._parse_tieba_item(item, search_keyword)
                if post_data:
                    posts.append(post_data)
            except Exception as e:
                logger.warning(f"Failed to parse Tieba item: {e}")
                continue

        logger.info(f"Parsed {len(posts)} Tieba posts")
        return posts

    async def _parse_tieba_item(self, item, search_keyword: str) -> dict | None:
        """Parse a single Tieba search result."""
        try:
            # Extract title and link
            title_el = await item.query_selector("a.bluelink, .p_title a, a[href*='tieba.baidu.com/p/']")
            if not title_el:
                return None

            title = await title_el.text_content()
            title = title.strip() if title else ""
            if not title:
                return None

            href = await title_el.get_attribute("href")
            source_url = href
            if source_url and not source_url.startswith("http"):
                source_url = f"https://tieba.baidu.com{source_url}"

            # Extract source_id from URL
            source_id = ""
            if source_url:
                match = re.search(r"/p/(\d+)", source_url)
                if match:
                    source_id = f"tieba_{match.group(1)}"

            if not source_id:
                source_id = f"tieba_{hash(title)}"

            # Extract content
            content_el = await item.query_selector(".p_content, .content, .post-content")
            content = ""
            if content_el:
                content = await content_el.text_content()
                content = content.strip() if content else ""

            if not content:
                content = title

            # Extract author
            author_el = await item.query_selector(".p_author_name, .author, .username")
            author = ""
            if author_el:
                author = await author_el.text_content()
                author = author.strip() if author else ""

            # Extract forum name
            forum_el = await item.query_selector(".p_forum, .forum-name, a[href*='kw=']")
            topic = ""
            if forum_el:
                topic = await forum_el.text_content()
                topic = topic.strip() if topic else ""
                topic = topic.replace("吧", "")  # Remove "吧" suffix

            # Extract replies
            replies_el = await item.query_selector(".p_reply, .reply-num")
            replies_count = 0
            if replies_el:
                replies_text = await replies_el.text_content()
                if replies_text:
                    match = re.search(r"(\d+)", replies_text)
                    if match:
                        replies_count = int(match.group(1))

            return {
                "source_id": source_id,
                "source_url": source_url,
                "title": title,
                "content": content,
                "author": author,
                "topic": f"{topic}吧" if topic else "贴吧",
                "replies_count": replies_count,
                "post_type": "post",
                "search_keyword": search_keyword,
                "posted_at": None,
            }

        except Exception as e:
            logger.warning(f"Error parsing Tieba item: {e}")
            return None

    async def _save_posts(
        self, db: AsyncSession, posts_data: list[dict], city_name: str | None
    ) -> int:
        """Save forum posts to database."""
        saved_count = 0

        for post_data in posts_data:
            try:
                post = ForumPost(
                    data_source_id=self.data_source_id,
                    city_id=self.city_id,
                    crawl_task_id=UUID(self.config.get("task_id")) if self.config.get("task_id") else None,
                    source_id=post_data["source_id"],
                    source_url=post_data.get("source_url"),
                    post_type=post_data.get("post_type", "post"),
                    title=post_data.get("title"),
                    content=post_data["content"],
                    author=post_data.get("author"),
                    topic=post_data.get("topic"),
                    replies_count=post_data.get("replies_count", 0),
                    search_keyword=post_data.get("search_keyword"),
                    posted_at=post_data.get("posted_at"),
                )
                db.add(post)
                saved_count += 1

            except Exception as e:
                logger.warning(f"Failed to save post: {e}")
                continue

        await db.commit()
        logger.info(f"Saved {saved_count} forum posts to database")
        return saved_count
