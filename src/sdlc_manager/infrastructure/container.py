from __future__ import annotations

from dataclasses import dataclass

from ..application.services.event_processor import SdlcEventProcessor
from ..application.services.sdlc_service import SdlcService
from ..application.services.workflow_service import WorkflowService
from ..config import Settings
from ..engines.policy_engine import PolicyEngine
from ..engines.practice_engine import PracticeEngine
from ..engines.workflow_engine import WorkflowEngine
from .database.db import create_database_engine, create_schema, create_session_factory
from .policy_loader.loader import PolicyLoader
from .repositories.sqlalchemy_repositories import (
    SqlAlchemyAuditRepository,
    SqlAlchemyEvaluationRepository,
    SqlAlchemyEventRepository,
    SqlAlchemyEvidenceRepository,
    SqlAlchemyExperienceRepository,
    SqlAlchemyPracticeRepository,
    SqlAlchemyProjectRepository,
    SqlAlchemySprintRepository,
    SqlAlchemyUserStoryRepository,
    SqlAlchemyWorkflowRepository,
)
from .sddnxp.reader import SddnxpReader
from .workflow.loader import WorkflowInitializer, load_workflow


@dataclass(slots=True)
class ApplicationContainer:
    service: SdlcService
    policy_engine: PolicyEngine
    workflow_service: WorkflowService
    workflow_engine: WorkflowEngine
    event_processor: SdlcEventProcessor


def build_container(settings: Settings, initialize_schema: bool = True) -> ApplicationContainer:
    engine = create_database_engine(settings.database_url)
    if initialize_schema:
        create_schema(engine)
    factory = create_session_factory(engine)
    projects = SqlAlchemyProjectRepository(factory)
    workflow_repository = SqlAlchemyWorkflowRepository(factory)
    default_workflow = WorkflowInitializer(workflow_repository, projects).install(
        load_workflow(settings.resolve_path(settings.workflow_template_path))
    )
    policies = PolicyLoader(settings.resolved_policy_paths()).load()
    policy_engine = PolicyEngine(policies)
    practice_repository = SqlAlchemyPracticeRepository(factory)
    practice_engine = PracticeEngine(practice_repository.list(include_unapproved=True))
    workflow_engine = WorkflowEngine()
    audit_repository = SqlAlchemyAuditRepository(factory)
    event_repository = SqlAlchemyEventRepository(factory)
    service = SdlcService(
        projects=projects,
        sprints=SqlAlchemySprintRepository(factory),
        stories=SqlAlchemyUserStoryRepository(factory),
        experiences=SqlAlchemyExperienceRepository(factory),
        evidences=SqlAlchemyEvidenceRepository(factory),
        evaluations=SqlAlchemyEvaluationRepository(factory),
        policy_engine=policy_engine,
        practices=practice_repository,
        practice_engine=practice_engine,
        workflows=workflow_repository,
        workflow_engine=workflow_engine,
        audits=audit_repository,
        default_workflow_id=default_workflow.id,
    )
    return ApplicationContainer(
        service=service,
        policy_engine=policy_engine,
        workflow_service=WorkflowService(workflow_repository, projects),
        workflow_engine=workflow_engine,
        event_processor=SdlcEventProcessor(
            service,
            event_repository,
            audit_repository,
            SddnxpReader(settings.project_root),
        ),
    )
