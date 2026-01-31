from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    items: list[T]
    total: int
    skip: int
    limit: int

    @property
    def pages(self) -> int:
        if self.limit <= 0:
            return 0
        return (self.total + self.limit - 1) // self.limit

    @property
    def page(self) -> int:
        if self.limit <= 0:
            return 1
        return (self.skip // self.limit) + 1


class MessageResponse(BaseModel):
    message: str
