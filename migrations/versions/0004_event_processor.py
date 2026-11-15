"""Agrega persistencia idempotente para eventos normalizados del SDLC."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_event_processor"
down_revision: str | None = "0003_workflow_enforcement"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("TEXPERIENCIA", sa.Column("CPROYECTO", sa.String(36)))
    op.create_index("IFKEXPERPROY", "TEXPERIENCIA", ["CPROYECTO"])
    op.create_table(
        "TEVENTOSDLC",
        sa.Column("CEVENTO", sa.String(36), primary_key=True),
        sa.Column("HUELLA", sa.String(64), nullable=False),
        sa.Column("ESTADO", sa.String(40), nullable=False),
        sa.Column("RESULTADO", sa.Text(), nullable=False),
        sa.Column("FCREACION", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("TEVENTOSDLC")
    op.drop_index("IFKEXPERPROY", table_name="TEXPERIENCIA")
    op.drop_column("TEXPERIENCIA", "CPROYECTO")
