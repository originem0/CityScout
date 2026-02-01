"""爬虫进度和错误模型.

定义结构化的爬虫状态、进度和错误信息，用于可观测性。
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CrawlState(str, Enum):
    """爬虫状态枚举."""
    INIT = "init"  # 初始化中
    CONNECTING = "connecting"  # 连接页面中
    LOADING = "loading"  # 加载内容中
    PARSING = "parsing"  # 解析数据中
    SAVING = "saving"  # 保存数据中
    PAGINATING = "paginating"  # 翻页中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class ErrorType(str, Enum):
    """错误类型枚举."""
    TIMEOUT = "timeout"  # 超时
    BLOCKED = "blocked"  # 被封禁/403
    CAPTCHA = "captcha"  # 验证码
    PARSE_ERROR = "parse_error"  # 解析错误
    NETWORK = "network"  # 网络错误
    RATE_LIMIT = "rate_limit"  # 频率限制/429
    DB_ERROR = "db_error"  # 数据库错误
    PROXY_ERROR = "proxy_error"  # 代理错误
    UNKNOWN = "unknown"  # 未知错误


# 错误类型对应的可操作建议
ERROR_SUGGESTIONS = {
    ErrorType.TIMEOUT: "增加超时时间或检查网络连接",
    ErrorType.BLOCKED: "启用或更换代理IP，增加请求间隔",
    ErrorType.CAPTCHA: "暂停爬取，等待一段时间后重试，或手动处理验证码",
    ErrorType.PARSE_ERROR: "检查页面结构是否变化，更新选择器",
    ErrorType.NETWORK: "检查网络连接，稍后重试",
    ErrorType.RATE_LIMIT: "降低请求频率，增加请求间隔",
    ErrorType.DB_ERROR: "检查数据库连接和表结构",
    ErrorType.PROXY_ERROR: "代理不可用，尝试更换代理",
    ErrorType.UNKNOWN: "查看详细日志进行排查",
}


@dataclass
class CrawlError:
    """单个爬虫错误."""
    error_type: ErrorType
    message: str
    url: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    recoverable: bool = True
    suggestion: str = ""

    def __post_init__(self):
        # 如果没有提供建议，使用默认建议
        if not self.suggestion:
            self.suggestion = ERROR_SUGGESTIONS.get(self.error_type, "")

    def to_dict(self) -> dict:
        """转换为字典格式."""
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "url": self.url,
            "timestamp": self.timestamp.isoformat(),
            "recoverable": self.recoverable,
            "suggestion": self.suggestion,
        }


@dataclass
class CrawlProgress:
    """爬虫进度状态."""
    task_id: str
    state: CrawlState = CrawlState.INIT
    current_page: int = 0
    total_pages: int | None = None
    items_found: int = 0
    items_saved: int = 0
    items_failed: int = 0
    current_url: str = ""
    errors: list[CrawlError] = field(default_factory=list)
    started_at: datetime | None = None
    _last_percentage: int = 0

    def __post_init__(self):
        if self.started_at is None:
            self.started_at = datetime.now()

    @property
    def percentage(self) -> int:
        """计算当前进度百分比."""
        if self.state == CrawlState.COMPLETED:
            return 100
        if self.state == CrawlState.FAILED:
            return self._last_percentage
        if self.state == CrawlState.INIT:
            return 0

        # 基于页数计算进度 (0-80%)
        if self.total_pages and self.total_pages > 0:
            page_progress = int((self.current_page / self.total_pages) * 80)
        elif self.current_page > 0:
            page_progress = min(50, self.current_page * 10)
        else:
            page_progress = 5

        # 状态加成
        state_bonus = {
            CrawlState.CONNECTING: 2,
            CrawlState.LOADING: 5,
            CrawlState.PARSING: 10,
            CrawlState.SAVING: 15,
            CrawlState.PAGINATING: 0,
        }.get(self.state, 0)

        self._last_percentage = min(95, page_progress + state_bonus)
        return self._last_percentage

    @property
    def success_rate(self) -> float:
        """计算成功率."""
        total = self.items_saved + self.items_failed
        if total == 0:
            return 0.0
        return self.items_saved / total

    @property
    def has_errors(self) -> bool:
        """是否有错误."""
        return len(self.errors) > 0

    @property
    def last_error(self) -> CrawlError | None:
        """获取最后一个错误."""
        return self.errors[-1] if self.errors else None

    @property
    def error_summary(self) -> dict[str, int]:
        """按错误类型汇总."""
        summary: dict[str, int] = {}
        for error in self.errors:
            key = error.error_type.value
            summary[key] = summary.get(key, 0) + 1
        return summary

    def update_state(self, state: CrawlState, url: str = ""):
        """更新状态."""
        self.state = state
        if url:
            self.current_url = url

    def add_error(
        self,
        error_type: ErrorType,
        message: str,
        url: str = "",
        recoverable: bool = True,
    ) -> CrawlError:
        """添加错误."""
        error = CrawlError(
            error_type=error_type,
            message=message,
            url=url or self.current_url,
            recoverable=recoverable,
        )
        self.errors.append(error)
        return error

    def increment_found(self, count: int = 1):
        """增加找到的项目数."""
        self.items_found += count

    def increment_saved(self, count: int = 1):
        """增加保存的项目数."""
        self.items_saved += count

    def increment_failed(self, count: int = 1):
        """增加失败的项目数."""
        self.items_failed += count

    def set_page(self, current: int, total: int | None = None):
        """设置分页信息."""
        self.current_page = current
        if total is not None:
            self.total_pages = total

    def complete(self):
        """标记为完成."""
        self.state = CrawlState.COMPLETED

    def fail(self, error_type: ErrorType, message: str, url: str = ""):
        """标记为失败并记录错误."""
        self.add_error(error_type, message, url, recoverable=False)
        self.state = CrawlState.FAILED

    def to_dict(self) -> dict:
        """转换为字典格式（用于API响应和数据库存储）."""
        return {
            "task_id": self.task_id,
            "state": self.state.value,
            "percentage": self.percentage,
            "current_page": self.current_page,
            "total_pages": self.total_pages,
            "items_found": self.items_found,
            "items_saved": self.items_saved,
            "items_failed": self.items_failed,
            "current_url": self.current_url,
            "success_rate": self.success_rate,
            "errors": [e.to_dict() for e in self.errors],
            "error_summary": self.error_summary,
            "started_at": self.started_at.isoformat() if self.started_at else None,
        }


def classify_exception(exception: Exception, url: str = "") -> CrawlError:
    """根据异常类型自动分类错误.

    Args:
        exception: 捕获的异常
        url: 相关URL

    Returns:
        CrawlError 对象
    """
    error_str = str(exception).lower()

    # 超时错误
    if "timeout" in error_str or "timed out" in error_str:
        return CrawlError(
            error_type=ErrorType.TIMEOUT,
            message=str(exception),
            url=url,
            recoverable=True,
        )

    # 网络错误
    if any(kw in error_str for kw in ["connection", "network", "dns", "refused", "reset"]):
        return CrawlError(
            error_type=ErrorType.NETWORK,
            message=str(exception),
            url=url,
            recoverable=True,
        )

    # 代理错误
    if any(kw in error_str for kw in ["proxy", "socks"]):
        return CrawlError(
            error_type=ErrorType.PROXY_ERROR,
            message=str(exception),
            url=url,
            recoverable=True,
        )

    # 403/封禁
    if "403" in error_str or "forbidden" in error_str or "blocked" in error_str:
        return CrawlError(
            error_type=ErrorType.BLOCKED,
            message=str(exception),
            url=url,
            recoverable=True,
        )

    # 429/频率限制
    if "429" in error_str or "rate limit" in error_str or "too many" in error_str:
        return CrawlError(
            error_type=ErrorType.RATE_LIMIT,
            message=str(exception),
            url=url,
            recoverable=True,
        )

    # 验证码
    if any(kw in error_str for kw in ["captcha", "验证码", "verify", "robot"]):
        return CrawlError(
            error_type=ErrorType.CAPTCHA,
            message=str(exception),
            url=url,
            recoverable=False,
        )

    # 数据库错误
    if any(kw in error_str for kw in ["database", "db", "sqlalchemy", "postgres"]):
        return CrawlError(
            error_type=ErrorType.DB_ERROR,
            message=str(exception),
            url=url,
            recoverable=False,
        )

    # 默认为未知错误
    return CrawlError(
        error_type=ErrorType.UNKNOWN,
        message=str(exception),
        url=url,
        recoverable=True,
    )
