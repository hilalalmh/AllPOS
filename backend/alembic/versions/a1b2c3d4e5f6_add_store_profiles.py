"""add store_profiles singleton

Revision ID: a1b2c3d4e5f6
Revises: 3ed605c47695
Create Date: 2026-09-23 10:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '3ed605c47695'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'store_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('store_name', sa.String(length=100), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=30), nullable=True),
        sa.Column('footer', sa.String(length=120), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.execute(
        "INSERT INTO store_profiles (id, store_name, footer) "
        "VALUES (1, 'SISTEM POS', 'TERIMA KASIH ~ SILAHKAN DATANG KEMBALI') "
        "ON CONFLICT (id) DO NOTHING"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('store_profiles')
