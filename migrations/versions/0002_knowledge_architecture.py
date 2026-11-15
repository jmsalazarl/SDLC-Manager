"""Additive knowledge architecture for workflows and engineering practices."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_knowledge_architecture"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "TFLUJOSDLC",
        sa.Column("CFLUJOSDLC", sa.String(36), primary_key=True),
        sa.Column("CODIGO", sa.String(80), nullable=False),
        sa.Column("NOMBRE", sa.String(200), nullable=False),
        sa.Column("VERSION", sa.String(40), nullable=False),
        sa.Column("ESTADO", sa.String(40), nullable=False),
        sa.Column("FUENTE", sa.String(200), nullable=False),
        sa.Column("FCREACION", sa.DateTime(), nullable=False),
        sa.Column("FACTUALIZACION", sa.DateTime(), nullable=False),
    )
    op.create_index("IUKFLUJOCODVER", "TFLUJOSDLC", ["CODIGO", "VERSION"], unique=True)
    op.create_table(
        "TETAPASDLC",
        sa.Column("CETAPADLC", sa.String(36), primary_key=True),
        sa.Column(
            "CFLUJOSDLC",
            sa.String(36),
            sa.ForeignKey("TFLUJOSDLC.CFLUJOSDLC"),
            nullable=False,
        ),
        sa.Column("CODIGO", sa.String(80), nullable=False),
        sa.Column("NOMBRE", sa.String(200), nullable=False),
        sa.Column("DESCRIPCION", sa.Text(), nullable=False),
        sa.Column("ORDEN", sa.Integer(), nullable=False),
        sa.Column("ESOBLIGATORIA", sa.Boolean(), nullable=False),
    )
    op.create_index("IFKETAPAFLUJ", "TETAPASDLC", ["CFLUJOSDLC"])
    op.create_table(
        "TGATESDLC",
        sa.Column("CGATEDLC", sa.String(36), primary_key=True),
        sa.Column(
            "CETAPADLC",
            sa.String(36),
            sa.ForeignKey("TETAPASDLC.CETAPADLC"),
            nullable=False,
        ),
        sa.Column("CODIGO", sa.String(80), nullable=False),
        sa.Column("NOMBRE", sa.String(200), nullable=False),
        sa.Column("ESOBLIGATORIO", sa.Boolean(), nullable=False),
        sa.Column("VERIFICACIONES", sa.Text(), nullable=False),
        sa.Column("CONDICIONES", sa.Text(), nullable=False),
        sa.Column("HABILITADA", sa.Boolean(), nullable=False),
    )
    op.create_index("IFKGATEETAPA", "TGATESDLC", ["CETAPADLC"])
    op.create_table(
        "TEXCEPCIONDLC",
        sa.Column("CEXCEPCIONDLC", sa.String(36), primary_key=True),
        sa.Column(
            "CFLUJOSDLC",
            sa.String(36),
            sa.ForeignKey("TFLUJOSDLC.CFLUJOSDLC"),
            nullable=False,
        ),
        sa.Column("CODIGOGATE", sa.String(80), nullable=False),
        sa.Column("CODIGO", sa.String(80), nullable=False),
        sa.Column("MOTIVO", sa.Text(), nullable=False),
        sa.Column("CONDICION", sa.Text(), nullable=False),
        sa.Column("ESTADO", sa.String(40), nullable=False),
        sa.Column("APROBADOPOR", sa.String(160)),
        sa.Column("FAPROBACION", sa.DateTime()),
    )
    op.create_index("IFKEXCFLUJ", "TEXCEPCIONDLC", ["CFLUJOSDLC"])
    op.create_table(
        "TPRACTICA",
        sa.Column("CPRACTICA", sa.String(36), primary_key=True),
        sa.Column("TITULO", sa.String(200), nullable=False),
        sa.Column("CONTEXTO", sa.Text(), nullable=False),
        sa.Column("ACTIVADORES", sa.Text(), nullable=False),
        sa.Column("MENSAJEINTERVENCION", sa.Text(), nullable=False),
        sa.Column("SEVERIDAD", sa.String(40), nullable=False),
        sa.Column("ALCANCE", sa.String(40), nullable=False),
        sa.Column("CEXPERIENCIA", sa.String(36), sa.ForeignKey("TEXPERIENCIA.CEXPERIENCIA")),
        sa.Column("ESTADOAPROBACION", sa.String(40), nullable=False),
        sa.Column("HABILITADA", sa.Boolean(), nullable=False),
        sa.Column("APROBADOPOR", sa.String(160)),
        sa.Column("FAPROBACION", sa.DateTime()),
        sa.Column("FCREACION", sa.DateTime(), nullable=False),
        sa.Column("FACTUALIZACION", sa.DateTime(), nullable=False),
    )
    op.create_index("IFKPRACTEXPER", "TPRACTICA", ["CEXPERIENCIA"])
    with op.batch_alter_table("TPROYECTO", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("CFLUJOSDLC", sa.String(36)))
        batch_op.create_foreign_key(
            "FKPROYFLUJ",
            "TFLUJOSDLC",
            ["CFLUJOSDLC"],
            ["CFLUJOSDLC"],
        )
    op.create_index("IFKPROYFLUJ", "TPROYECTO", ["CFLUJOSDLC"])
    for column in (
        sa.Column("TIPOMEMORIA", sa.String(40)),
        sa.Column("TECNOLOGIA", sa.String(120)),
        sa.Column("CATEGORIA", sa.String(120)),
        sa.Column("ALCANCE", sa.String(40)),
        sa.Column("AUTOR", sa.String(160)),
        sa.Column("REVISADOPOR", sa.String(160)),
        sa.Column("FREVISION", sa.DateTime()),
        sa.Column("MEMORIASRELACIONADAS", sa.Text()),
    ):
        op.add_column("TEXPERIENCIA", column)
    op.execute("UPDATE TEXPERIENCIA SET TIPOMEMORIA = 'LESSON_LEARNED' WHERE TIPOMEMORIA IS NULL")
    op.execute("UPDATE TEXPERIENCIA SET ALCANCE = 'PERSONAL' WHERE ALCANCE IS NULL")
    op.execute(
        "UPDATE TEXPERIENCIA SET MEMORIASRELACIONADAS = '[]' WHERE MEMORIASRELACIONADAS IS NULL"
    )


def downgrade() -> None:
    for column in (
        "MEMORIASRELACIONADAS",
        "FREVISION",
        "REVISADOPOR",
        "AUTOR",
        "ALCANCE",
        "CATEGORIA",
        "TECNOLOGIA",
        "TIPOMEMORIA",
    ):
        op.drop_column("TEXPERIENCIA", column)
    op.drop_index("IFKPROYFLUJ", table_name="TPROYECTO")
    with op.batch_alter_table("TPROYECTO", recreate="always") as batch_op:
        batch_op.drop_constraint("FKPROYFLUJ", type_="foreignkey")
        batch_op.drop_column("CFLUJOSDLC")
    op.drop_index("IFKPRACTEXPER", table_name="TPRACTICA")
    op.drop_table("TPRACTICA")
    op.drop_index("IFKEXCFLUJ", table_name="TEXCEPCIONDLC")
    op.drop_table("TEXCEPCIONDLC")
    op.drop_index("IFKGATEETAPA", table_name="TGATESDLC")
    op.drop_table("TGATESDLC")
    op.drop_index("IFKETAPAFLUJ", table_name="TETAPASDLC")
    op.drop_table("TETAPASDLC")
    op.drop_index("IUKFLUJOCODVER", table_name="TFLUJOSDLC")
    op.drop_table("TFLUJOSDLC")
