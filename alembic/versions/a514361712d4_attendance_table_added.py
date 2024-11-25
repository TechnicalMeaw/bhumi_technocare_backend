"""attendance table added

Revision ID: a514361712d4
Revises: 246969b2bf50
Create Date: 2024-11-23 21:24:38.774121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a514361712d4'
down_revision: Union[str, None] = '246969b2bf50'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('attendance',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('photo', sa.String(), nullable=False),
    sa.Column('is_clock_in', sa.Boolean(), server_default=sa.text('True'), nullable=False),
    sa.Column('is_approved', sa.Boolean(), server_default=sa.text('False'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('Now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_attendance_user_id'), 'attendance', ['user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_attendance_user_id'), table_name='attendance')
    op.drop_table('attendance')
    # ### end Alembic commands ###