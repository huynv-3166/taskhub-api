"""normalize user roles

Revision ID: 2569dd0fdaaa
Revises: d8c7ac559a65
Create Date: 2026-07-22 13:06:55.276596

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "2569dd0fdaaa"
down_revision: Union[str, Sequence[str], None] = "d8c7ac559a65"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE users
            SET role = upper(role)
            WHERE upper(role) IN ('ADMIN', 'MEMBER')
            """
        )
    )

    op.create_check_constraint(
        "ck_users_role",
        "users",
        "role IN ('ADMIN', 'MEMBER')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_users_role",
        "users",
        type_="check",
    )

    op.execute(
        sa.text(
            """
            UPDATE users
            SET role = lower(role)
            WHERE role IN ('ADMIN', 'MEMBER')
            """
        )
    )
