"""add company review table and job rating fields

Revision ID: c7f2a8b3d5e9
Revises: b5e8f3a91c7d
Create Date: 2026-01-31 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c7f2a8b3d5e9'
down_revision: Union[str, None] = 'b5e8f3a91c7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create company_reviews table
    op.create_table(
        'company_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_name', sa.String(200), nullable=False),
        sa.Column('data_source_id', sa.Integer(), nullable=False),
        # 看准网评分字段
        sa.Column('overall_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('culture_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('management_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('salary_benefit_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('career_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('work_life_balance', sa.Numeric(3, 2), nullable=True),
        # Statistics
        sa.Column('review_count', sa.Integer(), nullable=True),
        sa.Column('recommend_rate', sa.Numeric(5, 2), nullable=True),
        # 职友集薪资分位数
        sa.Column('salary_p25', sa.Numeric(10, 2), nullable=True),
        sa.Column('salary_p50', sa.Numeric(10, 2), nullable=True),
        sa.Column('salary_p75', sa.Numeric(10, 2), nullable=True),
        sa.Column('salary_sample_count', sa.Integer(), nullable=True),
        # Metadata
        sa.Column('company_summary', sa.Text(), nullable=True),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('match_confidence', sa.Numeric(3, 2), nullable=True),
        sa.Column('crawled_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['data_source_id'], ['data_sources.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_company_reviews_company_name', 'company_reviews', ['company_name'], unique=True)

    # Add company rating fields to jobs table
    op.add_column('jobs', sa.Column('company_rating', sa.Numeric(3, 2), nullable=True))
    op.add_column('jobs', sa.Column('salary_percentile_25', sa.Numeric(10, 2), nullable=True))
    op.add_column('jobs', sa.Column('salary_percentile_50', sa.Numeric(10, 2), nullable=True))
    op.add_column('jobs', sa.Column('salary_percentile_75', sa.Numeric(10, 2), nullable=True))


def downgrade() -> None:
    # Remove columns from jobs table
    op.drop_column('jobs', 'salary_percentile_75')
    op.drop_column('jobs', 'salary_percentile_50')
    op.drop_column('jobs', 'salary_percentile_25')
    op.drop_column('jobs', 'company_rating')

    # Drop company_reviews table
    op.drop_index('ix_company_reviews_company_name', table_name='company_reviews')
    op.drop_table('company_reviews')
