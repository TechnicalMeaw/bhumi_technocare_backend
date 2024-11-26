from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision: str = '270b9dbc2086'
down_revision: Union[str, None] = '86a14b163549'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the Enum type
    bill_type_enum = sa.Enum('cash', 'credit', 'bill', name='billtype')
    bill_type_enum.create(op.get_bind())  # Explicitly create the type in the database

    # Add the new column with the Enum type
    op.add_column('bill', sa.Column('bill_type', bill_type_enum, nullable=False))
    op.create_index(op.f('ix_bill_bill_type'), 'bill', ['bill_type'], unique=False)

    # Add the new column in the complaints table
    op.add_column('complaints', sa.Column('is_started', sa.Boolean(), server_default=sa.text('False'), nullable=False))


def downgrade() -> None:
    # Remove the complaints column
    op.drop_column('complaints', 'is_started')

    # Remove the index and column from the bill table
    op.drop_index(op.f('ix_bill_bill_type'), table_name='bill')
    op.drop_column('bill', 'bill_type')

    # Drop the Enum type
    bill_type_enum = sa.Enum('cash', 'credit', 'bill', name='billtype')
    bill_type_enum.drop(op.get_bind())
