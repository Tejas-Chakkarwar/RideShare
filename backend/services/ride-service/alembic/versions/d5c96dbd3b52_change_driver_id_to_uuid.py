"""change_driver_id_to_uuid

Revision ID: d5c96dbd3b52
Revises: 
Create Date: 2026-01-09 01:48:53.771227

"""
from typing import Sequence, Union

from alembic import op
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd5c96dbd3b52'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('rides', 'driver_id',
               existing_type=sa.Integer(),
               type_=postgresql.UUID(as_uuid=True),
               existing_nullable=False,
               postgresql_using='driver_id::text::uuid')
    
    # Add 'in_progress' to enum
    op.execute("ALTER TYPE ridestatus ADD VALUE IF NOT EXISTS 'in_progress'")


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('rides', 'driver_id',
               existing_type=postgresql.UUID(as_uuid=True),
               type_=sa.Integer(),
               existing_nullable=False,
               postgresql_using='driver_id::text::int')
