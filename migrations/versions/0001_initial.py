"""Esquema inicial del MVP.

Revision ID: 0001_initial
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "TPROYECTO",
        sa.Column("CPROYECTO", sa.String(36), primary_key=True),
        sa.Column("NOMBRE", sa.String(200), nullable=False),
        sa.Column("DESCRIPCION", sa.Text()),
        sa.Column("FCREACION", sa.DateTime(), nullable=False),
        sa.Column("FACTUALIZACION", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "TSPRINT",
        sa.Column("CSPRINT", sa.String(36), primary_key=True),
        sa.Column("CPROYECTO", sa.String(36), sa.ForeignKey("TPROYECTO.CPROYECTO"), nullable=False),
        sa.Column("NOMBRE", sa.String(200), nullable=False),
        sa.Column("FINICIO", sa.Date()),
        sa.Column("FFIN", sa.Date()),
        sa.Column("ESTADO", sa.String(40), nullable=False),
    )
    op.create_index("IFKSPRINTPROY", "TSPRINT", ["CPROYECTO"])
    op.create_table(
        "THISTORIAUSUARIO",
        sa.Column("CHISTORIAUSUARIO", sa.String(36), primary_key=True),
        sa.Column("CPROYECTO", sa.String(36), sa.ForeignKey("TPROYECTO.CPROYECTO"), nullable=False),
        sa.Column("CSPRINT", sa.String(36), sa.ForeignKey("TSPRINT.CSPRINT")),
        sa.Column("REFERENCIAEXTERNA", sa.String(120)),
        sa.Column("TITULO", sa.String(300), nullable=False),
        sa.Column("DESCRIPCION", sa.Text()),
        sa.Column("CRITERIOSACEPTACION", sa.Text(), nullable=False),
        sa.Column("DEPENDENCIAS", sa.Text(), nullable=False),
        sa.Column("ESTADO", sa.String(40), nullable=False),
        sa.Column("FCREACION", sa.DateTime(), nullable=False),
        sa.Column("FACTUALIZACION", sa.DateTime(), nullable=False),
    )
    op.create_index("IFKHUCPROY", "THISTORIAUSUARIO", ["CPROYECTO"])
    op.create_index("IFKHUCSPRINT", "THISTORIAUSUARIO", ["CSPRINT"])
    op.create_table(
        "TEXPERIENCIA",
        sa.Column("CEXPERIENCIA", sa.String(36), primary_key=True),
        sa.Column("TITULO", sa.String(300), nullable=False),
        sa.Column("CONTEXTO", sa.Text(), nullable=False),
        sa.Column("PROBLEMA", sa.Text(), nullable=False),
        sa.Column("CAUSARAIZ", sa.Text(), nullable=False),
        sa.Column("SOLUCION", sa.Text(), nullable=False),
        sa.Column("LECCIONAPRENDIDA", sa.Text(), nullable=False),
        sa.Column("COMPONENTE", sa.String(160)),
        sa.Column("ETIQUETAS", sa.Text(), nullable=False),
        sa.Column("REGLASRELACIONADAS", sa.Text(), nullable=False),
        sa.Column("ESTADOREVISION", sa.String(40), nullable=False),
        sa.Column("FCREACION", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "TEVIDENCIA",
        sa.Column("CEVIDENCIA", sa.String(36), primary_key=True),
        sa.Column("CPROYECTO", sa.String(36), sa.ForeignKey("TPROYECTO.CPROYECTO"), nullable=False),
        sa.Column(
            "CHISTORIAUSUARIO",
            sa.String(36),
            sa.ForeignKey("THISTORIAUSUARIO.CHISTORIAUSUARIO"),
            nullable=False,
        ),
        sa.Column("CPOLITICA", sa.String(120), nullable=False),
        sa.Column("TIPOEVIDENCIA", sa.String(120), nullable=False),
        sa.Column("REFERENCIA", sa.String(500), nullable=False),
        sa.Column("ESTADOVERIFICACION", sa.String(40), nullable=False),
        sa.Column("VERIFICADOPOR", sa.String(160)),
        sa.Column("FVERIFICACION", sa.DateTime()),
        sa.Column("FCREACION", sa.DateTime(), nullable=False),
    )
    op.create_index("IFKEVIDPROY", "TEVIDENCIA", ["CPROYECTO"])
    op.create_index("IFKEVIDHU", "TEVIDENCIA", ["CHISTORIAUSUARIO"])
    op.create_index("IEVIDPOL", "TEVIDENCIA", ["CPOLITICA"])
    op.create_table(
        "TEVALUACIONPOLITICA",
        sa.Column("CEVALUACION", sa.String(36), primary_key=True),
        sa.Column("CPROYECTO", sa.String(36), sa.ForeignKey("TPROYECTO.CPROYECTO"), nullable=False),
        sa.Column(
            "CHISTORIAUSUARIO",
            sa.String(36),
            sa.ForeignKey("THISTORIAUSUARIO.CHISTORIAUSUARIO"),
        ),
        sa.Column("PUERTA", sa.String(80), nullable=False),
        sa.Column("REGLASACTIVADAS", sa.Text(), nullable=False),
        sa.Column("RESULTADO", sa.String(20), nullable=False),
        sa.Column("EVIDENCIASFALTANTES", sa.Text(), nullable=False),
        sa.Column("EXPLICACION", sa.Text(), nullable=False),
        sa.Column("FEVALUACION", sa.DateTime(), nullable=False),
    )
    op.create_index("IFKEVALPROY", "TEVALUACIONPOLITICA", ["CPROYECTO"])
    op.create_table(
        "TAUDITORIA",
        sa.Column("SAUDITORIA", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("TIPOEVENTO", sa.String(80), nullable=False),
        sa.Column("CPROYECTO", sa.String(36)),
        sa.Column("CENTIDAD", sa.String(120)),
        sa.Column("DETALLE", sa.Text(), nullable=False),
        sa.Column("FCREACION", sa.DateTime(), nullable=False),
    )
    op.create_index("IAUDITPROY", "TAUDITORIA", ["CPROYECTO"])


def downgrade() -> None:
    op.drop_index("IAUDITPROY", table_name="TAUDITORIA")
    op.drop_table("TAUDITORIA")
    op.drop_index("IFKEVALPROY", table_name="TEVALUACIONPOLITICA")
    op.drop_table("TEVALUACIONPOLITICA")
    op.drop_index("IEVIDPOL", table_name="TEVIDENCIA")
    op.drop_index("IFKEVIDHU", table_name="TEVIDENCIA")
    op.drop_index("IFKEVIDPROY", table_name="TEVIDENCIA")
    op.drop_table("TEVIDENCIA")
    op.drop_table("TEXPERIENCIA")
    op.drop_index("IFKHUCSPRINT", table_name="THISTORIAUSUARIO")
    op.drop_index("IFKHUCPROY", table_name="THISTORIAUSUARIO")
    op.drop_table("THISTORIAUSUARIO")
    op.drop_index("IFKSPRINTPROY", table_name="TSPRINT")
    op.drop_table("TSPRINT")
    op.drop_table("TPROYECTO")
