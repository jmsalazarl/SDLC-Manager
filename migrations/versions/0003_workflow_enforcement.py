"""Agrega trazabilidad de excepciones y aislamiento de practicas."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_workflow_enforcement"
down_revision: str | None = "0002_knowledge_architecture"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("TEXCEPCIONDLC") as batch_op:
        batch_op.add_column(sa.Column("RESPONSABLE", sa.String(160)))
        batch_op.add_column(sa.Column("FINICIO", sa.DateTime()))
        batch_op.add_column(sa.Column("FFIN", sa.DateTime()))
        batch_op.add_column(sa.Column("FUENTEAPROBACION", sa.String(160)))
        batch_op.add_column(sa.Column("REFERENCIAAPROBACION", sa.String(200)))
    with op.batch_alter_table("TPRACTICA") as batch_op:
        batch_op.add_column(sa.Column("CPROYECTO", sa.String(36)))
        batch_op.add_column(sa.Column("PROPIETARIO", sa.String(160)))
        batch_op.add_column(sa.Column("CORGANIZACION", sa.String(160)))
    op.create_index("IFKPRACTPROY", "TPRACTICA", ["CPROYECTO"])


def downgrade() -> None:
    op.drop_index("IFKPRACTPROY", table_name="TPRACTICA")
    with op.batch_alter_table("TPRACTICA") as batch_op:
        batch_op.drop_column("CORGANIZACION")
        batch_op.drop_column("PROPIETARIO")
        batch_op.drop_column("CPROYECTO")
    with op.batch_alter_table("TEXCEPCIONDLC") as batch_op:
        batch_op.drop_column("REFERENCIAAPROBACION")
        batch_op.drop_column("FUENTEAPROBACION")
        batch_op.drop_column("FFIN")
        batch_op.drop_column("FINICIO")
        batch_op.drop_column("RESPONSABLE")
