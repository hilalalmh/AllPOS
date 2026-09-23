"""add transactions.local_ref idempotency key

Revision ID: b7c8d9e0a1b2
Revises: a1b2c3d4e5f6
Create Date: 2026-09-23 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0a1b2'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'transactions',
        sa.Column('local_ref', sa.String(length=64), nullable=True),
    )
    op.create_index(
        'ix_transactions_local_ref', 'transactions', ['local_ref'], unique=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_transactions_local_ref', table_name='transactions')
    op.drop_column('transactions', 'local_ref')