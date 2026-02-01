"""add task progress fields

Revision ID: b5e8f3a91c7d
Revises: a26821c6492e
Create Date: 2024-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b5e8f3a91c7d'
down_revision: Union[str, None] = 'a26821c6492e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加细粒度进度跟踪字段
    op.add_column('crawl_tasks', sa.Column('current_state', sa.String(30), nullable=False, server_default='init'))
    op.add_column('crawl_tasks', sa.Column('current_page', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('crawl_tasks', sa.Column('total_pages', sa.Integer(), nullable=True))
    op.add_column('crawl_tasks', sa.Column('items_found', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('crawl_tasks', sa.Column('items_failed', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('crawl_tasks', sa.Column('error_type', sa.String(30), nullable=True))
    op.add_column('crawl_tasks', sa.Column('error_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('crawl_tasks', 'error_details')
    op.drop_column('crawl_tasks', 'error_type')
    op.drop_column('crawl_tasks', 'items_failed')
    op.drop_column('crawl_tasks', 'items_found')
    op.drop_column('crawl_tasks', 'total_pages')
    op.drop_column('crawl_tasks', 'current_page')
    op.drop_column('crawl_tasks', 'current_state')
