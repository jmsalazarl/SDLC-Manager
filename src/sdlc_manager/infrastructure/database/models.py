from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ProjectRecord(Base):
    __tablename__ = "TPROYECTO"

    id: Mapped[str] = mapped_column("CPROYECTO", String(36), primary_key=True)
    name: Mapped[str] = mapped_column("NOMBRE", String(200), nullable=False)
    description: Mapped[str | None] = mapped_column("DESCRIPCION", Text)
    workflow_id: Mapped[str | None] = mapped_column(
        "CFLUJOSDLC", String(36), ForeignKey("TFLUJOSDLC.CFLUJOSDLC"), index=True
    )
    created_at: Mapped[datetime] = mapped_column("FCREACION", DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column("FACTUALIZACION", DateTime, nullable=False)


class SprintRecord(Base):
    __tablename__ = "TSPRINT"

    id: Mapped[str] = mapped_column("CSPRINT", String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        "CPROYECTO", String(36), ForeignKey("TPROYECTO.CPROYECTO"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column("NOMBRE", String(200), nullable=False)
    start_date: Mapped[date | None] = mapped_column("FINICIO", Date)
    end_date: Mapped[date | None] = mapped_column("FFIN", Date)
    status: Mapped[str] = mapped_column("ESTADO", String(40), nullable=False)


class UserStoryRecord(Base):
    __tablename__ = "THISTORIAUSUARIO"

    id: Mapped[str] = mapped_column("CHISTORIAUSUARIO", String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        "CPROYECTO", String(36), ForeignKey("TPROYECTO.CPROYECTO"), nullable=False, index=True
    )
    sprint_id: Mapped[str | None] = mapped_column(
        "CSPRINT", String(36), ForeignKey("TSPRINT.CSPRINT"), index=True
    )
    external_reference: Mapped[str | None] = mapped_column("REFERENCIAEXTERNA", String(120))
    title: Mapped[str] = mapped_column("TITULO", String(300), nullable=False)
    description: Mapped[str | None] = mapped_column("DESCRIPCION", Text)
    acceptance_criteria: Mapped[str] = mapped_column("CRITERIOSACEPTACION", Text, nullable=False)
    dependencies: Mapped[str] = mapped_column("DEPENDENCIAS", Text, nullable=False)
    status: Mapped[str] = mapped_column("ESTADO", String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column("FCREACION", DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column("FACTUALIZACION", DateTime, nullable=False)


class ExperienceRecord(Base):
    __tablename__ = "TEXPERIENCIA"

    id: Mapped[str] = mapped_column("CEXPERIENCIA", String(36), primary_key=True)
    title: Mapped[str] = mapped_column("TITULO", String(300), nullable=False)
    context: Mapped[str] = mapped_column("CONTEXTO", Text, nullable=False)
    problem: Mapped[str] = mapped_column("PROBLEMA", Text, nullable=False)
    root_cause: Mapped[str] = mapped_column("CAUSARAIZ", Text, nullable=False)
    solution: Mapped[str] = mapped_column("SOLUCION", Text, nullable=False)
    lesson_learned: Mapped[str] = mapped_column("LECCIONAPRENDIDA", Text, nullable=False)
    component: Mapped[str | None] = mapped_column("COMPONENTE", String(160))
    tags: Mapped[str] = mapped_column("ETIQUETAS", Text, nullable=False)
    related_policy_ids: Mapped[str] = mapped_column("REGLASRELACIONADAS", Text, nullable=False)
    review_status: Mapped[str] = mapped_column("ESTADOREVISION", String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column("FCREACION", DateTime, nullable=False)
    memory_type: Mapped[str | None] = mapped_column("TIPOMEMORIA", String(40))
    technology: Mapped[str | None] = mapped_column("TECNOLOGIA", String(120))
    category: Mapped[str | None] = mapped_column("CATEGORIA", String(120))
    scope: Mapped[str | None] = mapped_column("ALCANCE", String(40))
    project_id: Mapped[str | None] = mapped_column("CPROYECTO", String(36), index=True)
    author: Mapped[str | None] = mapped_column("AUTOR", String(160))
    reviewed_by: Mapped[str | None] = mapped_column("REVISADOPOR", String(160))
    reviewed_at: Mapped[datetime | None] = mapped_column("FREVISION", DateTime)
    related_experience_ids: Mapped[str | None] = mapped_column("MEMORIASRELACIONADAS", Text)


class EvidenceRecord(Base):
    __tablename__ = "TEVIDENCIA"

    id: Mapped[str] = mapped_column("CEVIDENCIA", String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        "CPROYECTO", String(36), ForeignKey("TPROYECTO.CPROYECTO"), nullable=False, index=True
    )
    user_story_id: Mapped[str] = mapped_column(
        "CHISTORIAUSUARIO",
        String(36),
        ForeignKey("THISTORIAUSUARIO.CHISTORIAUSUARIO"),
        nullable=False,
        index=True,
    )
    policy_id: Mapped[str] = mapped_column("CPOLITICA", String(120), nullable=False, index=True)
    evidence_type: Mapped[str] = mapped_column("TIPOEVIDENCIA", String(120), nullable=False)
    reference: Mapped[str] = mapped_column("REFERENCIA", String(500), nullable=False)
    verification_status: Mapped[str] = mapped_column(
        "ESTADOVERIFICACION", String(40), nullable=False
    )
    verified_by: Mapped[str | None] = mapped_column("VERIFICADOPOR", String(160))
    verified_at: Mapped[datetime | None] = mapped_column("FVERIFICACION", DateTime)
    created_at: Mapped[datetime] = mapped_column("FCREACION", DateTime, nullable=False)


class EvaluationRecord(Base):
    __tablename__ = "TEVALUACIONPOLITICA"

    id: Mapped[str] = mapped_column("CEVALUACION", String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        "CPROYECTO", String(36), ForeignKey("TPROYECTO.CPROYECTO"), nullable=False, index=True
    )
    user_story_id: Mapped[str | None] = mapped_column(
        "CHISTORIAUSUARIO", String(36), ForeignKey("THISTORIAUSUARIO.CHISTORIAUSUARIO")
    )
    gate: Mapped[str] = mapped_column("PUERTA", String(80), nullable=False)
    triggered_rule_ids: Mapped[str] = mapped_column("REGLASACTIVADAS", Text, nullable=False)
    result: Mapped[str] = mapped_column("RESULTADO", String(20), nullable=False)
    missing_evidence: Mapped[str] = mapped_column("EVIDENCIASFALTANTES", Text, nullable=False)
    explanation: Mapped[str] = mapped_column("EXPLICACION", Text, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column("FEVALUACION", DateTime, nullable=False)


class AuditRecord(Base):
    __tablename__ = "TAUDITORIA"

    id: Mapped[int] = mapped_column("SAUDITORIA", Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column("TIPOEVENTO", String(80), nullable=False)
    project_id: Mapped[str | None] = mapped_column("CPROYECTO", String(36), index=True)
    entity_id: Mapped[str | None] = mapped_column("CENTIDAD", String(120))
    details: Mapped[str] = mapped_column("DETALLE", Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column("FCREACION", DateTime, nullable=False)


class EventRecord(Base):
    __tablename__ = "TEVENTOSDLC"

    id: Mapped[str] = mapped_column("CEVENTO", String(36), primary_key=True)
    payload_hash: Mapped[str] = mapped_column("HUELLA", String(64), nullable=False)
    status: Mapped[str] = mapped_column("ESTADO", String(40), nullable=False)
    result: Mapped[str] = mapped_column("RESULTADO", Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column("FCREACION", DateTime, nullable=False)


class WorkflowRecord(Base):
    __tablename__ = "TFLUJOSDLC"

    id: Mapped[str] = mapped_column("CFLUJOSDLC", String(36), primary_key=True)
    code: Mapped[str] = mapped_column("CODIGO", String(80), nullable=False)
    name: Mapped[str] = mapped_column("NOMBRE", String(200), nullable=False)
    version: Mapped[str] = mapped_column("VERSION", String(40), nullable=False)
    status: Mapped[str] = mapped_column("ESTADO", String(40), nullable=False)
    source: Mapped[str] = mapped_column("FUENTE", String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column("FCREACION", DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column("FACTUALIZACION", DateTime, nullable=False)


class StageRecord(Base):
    __tablename__ = "TETAPASDLC"

    id: Mapped[str] = mapped_column("CETAPADLC", String(36), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(
        "CFLUJOSDLC", String(36), ForeignKey("TFLUJOSDLC.CFLUJOSDLC"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column("CODIGO", String(80), nullable=False)
    name: Mapped[str] = mapped_column("NOMBRE", String(200), nullable=False)
    description: Mapped[str] = mapped_column("DESCRIPCION", Text, nullable=False)
    order: Mapped[int] = mapped_column("ORDEN", Integer, nullable=False)
    required: Mapped[bool] = mapped_column("ESOBLIGATORIA", Boolean, nullable=False)


class GateRecord(Base):
    __tablename__ = "TGATESDLC"

    id: Mapped[str] = mapped_column("CGATEDLC", String(36), primary_key=True)
    stage_id: Mapped[str] = mapped_column(
        "CETAPADLC", String(36), ForeignKey("TETAPASDLC.CETAPADLC"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column("CODIGO", String(80), nullable=False)
    name: Mapped[str] = mapped_column("NOMBRE", String(200), nullable=False)
    required: Mapped[bool] = mapped_column("ESOBLIGATORIO", Boolean, nullable=False)
    checks: Mapped[str] = mapped_column("VERIFICACIONES", Text, nullable=False)
    conditions: Mapped[str] = mapped_column("CONDICIONES", Text, nullable=False)
    enabled: Mapped[bool] = mapped_column("HABILITADA", Boolean, nullable=False)


class ExceptionRecord(Base):
    __tablename__ = "TEXCEPCIONDLC"

    id: Mapped[str] = mapped_column("CEXCEPCIONDLC", String(36), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(
        "CFLUJOSDLC", String(36), ForeignKey("TFLUJOSDLC.CFLUJOSDLC"), nullable=False, index=True
    )
    gate_code: Mapped[str] = mapped_column("CODIGOGATE", String(80), nullable=False)
    code: Mapped[str] = mapped_column("CODIGO", String(80), nullable=False)
    reason: Mapped[str] = mapped_column("MOTIVO", Text, nullable=False)
    condition: Mapped[str] = mapped_column("CONDICION", Text, nullable=False)
    status: Mapped[str] = mapped_column("ESTADO", String(40), nullable=False)
    approved_by: Mapped[str | None] = mapped_column("APROBADOPOR", String(160))
    approved_at: Mapped[datetime | None] = mapped_column("FAPROBACION", DateTime)
    responsible: Mapped[str | None] = mapped_column("RESPONSABLE", String(160))
    valid_from: Mapped[datetime | None] = mapped_column("FINICIO", DateTime)
    valid_until: Mapped[datetime | None] = mapped_column("FFIN", DateTime)
    approval_source: Mapped[str | None] = mapped_column("FUENTEAPROBACION", String(160))
    approval_reference: Mapped[str | None] = mapped_column("REFERENCIAAPROBACION", String(200))


class PracticeRecord(Base):
    __tablename__ = "TPRACTICA"

    id: Mapped[str] = mapped_column("CPRACTICA", String(36), primary_key=True)
    title: Mapped[str] = mapped_column("TITULO", String(200), nullable=False)
    context: Mapped[str] = mapped_column("CONTEXTO", Text, nullable=False)
    triggers: Mapped[str] = mapped_column("ACTIVADORES", Text, nullable=False)
    intervention_message: Mapped[str] = mapped_column("MENSAJEINTERVENCION", Text, nullable=False)
    severity: Mapped[str] = mapped_column("SEVERIDAD", String(40), nullable=False)
    scope: Mapped[str] = mapped_column("ALCANCE", String(40), nullable=False)
    project_id: Mapped[str | None] = mapped_column("CPROYECTO", String(36))
    owner_id: Mapped[str | None] = mapped_column("PROPIETARIO", String(160))
    organization_id: Mapped[str | None] = mapped_column("CORGANIZACION", String(160))
    source_experience_id: Mapped[str | None] = mapped_column(
        "CEXPERIENCIA", String(36), ForeignKey("TEXPERIENCIA.CEXPERIENCIA")
    )
    approval_status: Mapped[str] = mapped_column("ESTADOAPROBACION", String(40), nullable=False)
    enabled: Mapped[bool] = mapped_column("HABILITADA", Boolean, nullable=False)
    approved_by: Mapped[str | None] = mapped_column("APROBADOPOR", String(160))
    approved_at: Mapped[datetime | None] = mapped_column("FAPROBACION", DateTime)
    created_at: Mapped[datetime] = mapped_column("FCREACION", DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column("FACTUALIZACION", DateTime, nullable=False)
