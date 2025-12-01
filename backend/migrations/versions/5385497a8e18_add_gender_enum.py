"""add gender enum

Revision ID: 5385497a8e18
Revises: db5c953bb7f6
Create Date: 2025-12-01 18:03:26.399591

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5385497a8e18'
down_revision: Union[str, None] = 'db5c953bb7f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    gender_enum = sa.Enum('male', 'female', name='gender')
    gender_enum.create(op.get_bind(), checkfirst=True)

    op.execute("ALTER TABLE users ALTER COLUMN gender TYPE gender USING gender::gender")


def downgrade() -> None:
    op.execute("ALTER TABLE users ALTER COLUMN gender TYPE varchar USING gender::varchar")

    gender_enum = sa.Enum('male', 'female', name='gender')
    gender_enum.drop(op.get_bind(), checkfirst=True)
