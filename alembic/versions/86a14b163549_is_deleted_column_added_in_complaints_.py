"""is_deleted column added in complaints table

Revision ID: 86a14b163549
Revises: a514361712d4
Create Date: 2024-11-26 00:06:26.158976

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86a14b163549'
down_revision: Union[str, None] = 'a514361712d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('complaints', sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('False'), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('complaints', 'is_deleted')
    # ### end Alembic commands ###
