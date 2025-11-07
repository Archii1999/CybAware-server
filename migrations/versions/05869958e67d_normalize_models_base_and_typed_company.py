"""normalize models base and typed company

Revision ID: 05869958e67d
Revises: 9320a8cab801
Create Date: 2025-11-07 15:48:35.869280

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05869958e67d'
down_revision: Union[str, Sequence[str], None] = '9320a8cab801'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
