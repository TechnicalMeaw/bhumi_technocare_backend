"""asset_photo column added in bill table

Revision ID: eb2049249644
Revises: b739cb69368c
Create Date: 2024-11-30 18:42:10.578590

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb2049249644'
down_revision: Union[str, None] = 'b739cb69368c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bill', sa.Column('asset_photo', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('bill', 'asset_photo')
    # ### end Alembic commands ###