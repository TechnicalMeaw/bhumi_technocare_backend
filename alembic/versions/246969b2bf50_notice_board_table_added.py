"""notice_board table added

Revision ID: 246969b2bf50
Revises: c77da3c20c4c
Create Date: 2024-10-31 14:17:04.045099

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '246969b2bf50'
down_revision: Union[str, None] = 'c77da3c20c4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('notice_board',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('notice', sa.String(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('Now()'), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('True'), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notice_board_created_by'), 'notice_board', ['created_by'], unique=False)
    op.create_index(op.f('ix_notice_board_id'), 'notice_board', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_notice_board_id'), table_name='notice_board')
    op.drop_index(op.f('ix_notice_board_created_by'), table_name='notice_board')
    op.drop_table('notice_board')
    # ### end Alembic commands ###
