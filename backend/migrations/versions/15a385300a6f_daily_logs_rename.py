"""daily_logs rename

Revision ID: 15a385300a6f
Revises: eea756d01009
Create Date: 2025-12-07 23:36:48.649544

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15a385300a6f'
down_revision: Union[str, None] = 'eea756d01009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
