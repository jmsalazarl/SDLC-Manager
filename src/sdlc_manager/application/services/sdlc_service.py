from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID, uuid4

from ...domain.enums import (
    EvaluationResult,
    EvidenceStatus,
    KnowledgeScope,
    MemoryType,
    ReviewStatus,
)
from ...domain.models import (
    AuditEntry,
    EngineeringExperience,
    EngineeringPractice,
    Evidence,
    PolicyEvaluation,
    Project,
    Sprint,
    UserStory,
)
from ...domain.ports.repositories import (
    AuditRepository,
    EvaluationRepository,
    EvidenceRepository,
    ExperienceRepository,
    PracticeRepository,
    ProjectRepository,
    SprintRepository,
    UserStoryRepository,
    WorkflowRepository,
)
from ...engines.evidence_engine import validate_evidence_reference
from ...engines.experience_engine import ExperienceEngine
from ...engines.policy_engine import PolicyEngine
from ...engines.practice_engine import PracticeEngine
from ...engines.workflow_engine import WorkflowEngine


class ApplicationError(ValueError):
    """Error seguro y esperado de un caso de uso."""


class SdlcService:
    def __init__(
        self,
        projects: ProjectRepository,
        sprints: SprintRepository,
        stories: UserStoryRepository,
        experiences: ExperienceRepository,
        evidences: EvidenceRepository,
        evaluations: EvaluationRepository,
        policy_engine: PolicyEngine,
        practices: PracticeRepository,
        practice_engine: PracticeEngine,
        workflows: WorkflowRepository,
        workflow_engine: WorkflowEngine,
        audits: AuditRepository,
        default_workflow_id: UUID | None = None,
    ) -> None:
        self.projects = projects
        self.sprints = sprints
        self.stories = stories
        self.experiences = experiences
        self.evidences = evidences
        self.evaluations = evaluations
        self.policy_engine = policy_engine
        self.practices = practices
        self.practice_engine = practice_engine
        self.workflows = workflows
        self.workflow_engine = workflow_engine
        self.audits = audits
        self.default_workflow_id = default_workflow_id
        self.experience_engine = ExperienceEngine(experiences)

    def create_project(self, name: str, description: str | None = None) -> Project:
        project = Project(
            id=uuid4(),
            name=name,
            description=description,
            workflow_id=self.default_workflow_id,
        )
        return self.projects.save(project)

    def create_sprint(
        self,
        project_id: UUID,
        name: str,
        start_date: str | None = None,
        end_date: str | None = None,
        status: str = "PLANNED",
    ) -> Sprint:
        self._require_project(project_id)
        sprint = Sprint(
            id=uuid4(),
            project_id=project_id,
            name=name,
            start_date=date.fromisoformat(start_date) if start_date else None,
            end_date=date.fromisoformat(end_date) if end_date else None,
            status=status,
        )
        return self.sprints.save(sprint)

    def create_story(
        self,
        project_id: UUID,
        title: str,
        description: str | None = None,
        acceptance_criteria: list[str] | None = None,
        dependencies: list[dict[str, Any]] | None = None,
        sprint_id: UUID | None = None,
        external_reference: str | None = None,
        status: str = "DRAFT",
    ) -> UserStory:
        self._require_project(project_id)
        story = UserStory(
            id=uuid4(),
            project_id=project_id,
            sprint_id=sprint_id,
            external_reference=external_reference,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria or [],
            dependencies=dependencies or [],
            status=status,
        )
        return self.stories.save(story)

    def list_policies(
        self, status: str | None = None, severity: str | None = None
    ) -> list[dict[str, Any]]:
        return [
            self._policy_to_dict(policy)
            for policy in self.policy_engine.list_policies(status, severity)
        ]

    def get_applicable_rules(
        self,
        project_id: UUID,
        event: str,
        stage: str,
        changed_files: list[str],
        user_story_id: UUID | None = None,
        component: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        self._require_project(project_id)
        story = self._require_story(project_id, user_story_id) if user_story_id else None
        rule_context = self._story_context(story)
        rule_context.update(context or {})
        rule_context.update(
            {
                "project_id": str(project_id),
                "user_story_id": str(user_story_id) if user_story_id else None,
                "event": event,
                "stage": stage,
                "changed_files": changed_files,
                "component": component,
            }
        )
        return [
            {
                "id": item.rule.id,
                "name": item.rule.name,
                "severity": item.rule.severity,
                "action": item.rule.action,
                "target_gate": item.rule.target_gate,
                "description": item.rule.description,
            }
            for item in self.policy_engine.applicable_rules(rule_context)
        ]

    def evaluate_gate(
        self,
        project_id: UUID,
        user_story_id: UUID,
        gate: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._require_project(project_id)
        story = self._require_story(project_id, user_story_id)
        changed_files = (context or {}).get("changed_files", [])
        event = (context or {}).get("event") or self._infer_event(gate, changed_files)
        rule_context = self._story_context(story)
        rule_context.update(context or {})
        rule_context.update(
            {
                "project_id": str(project_id),
                "user_story_id": str(user_story_id),
                "event": event,
                "stage": (context or {}).get("stage", gate),
                "changed_files": changed_files,
            }
        )
        project = self._require_project(project_id)
        if project.workflow_id is None:
            raise ApplicationError("El proyecto no tiene workflow asignado")
        workflow = self.workflows.get(project.workflow_id)
        if workflow is None:
            raise ApplicationError("El workflow del proyecto no existe")
        configured_gate = next(
            (item for item in self.workflows.list_gates(workflow.id) if item.code == gate), None
        )
        if configured_gate is None:
            raise ApplicationError(f"Gate no configurado en el workflow: {gate}")
        exceptions = self.workflows.list_exceptions(workflow.id)
        rule_context["design_required"] = bool(rule_context.get("design_required", False))
        evidence = self.evidences.list_for_story(project_id, user_story_id)
        workflow_decision = self.workflow_engine.evaluate(
            configured_gate,
            rule_context,
            evidence,
            exceptions,
        )
        applicable = [
            item
            for item in self.policy_engine.applicable_rules(rule_context)
            if item.rule.target_gate == gate
        ]
        evidence_by_policy = {
            item.rule.id: {
                evidence.evidence_type
                for evidence in self.evidences.list_for_story_and_policy(
                    project_id, user_story_id, item.rule.id
                )
                if evidence.verification_status == EvidenceStatus.VERIFIED
            }
            for item in applicable
        }
        deduplicated_rules = {
            item.rule.id
            for item in applicable
            if set(item.rule.workflow_checks).intersection(configured_gate.checks)
        }
        decision = self.policy_engine.evaluate_gate(
            gate=gate,
            context=rule_context,
            evidence_by_policy=evidence_by_policy,
            evaluation_id=uuid4(),
            workflow_checks=set(configured_gate.checks),
            skipped_rule_ids=deduplicated_rules,
        )
        decision = self._merge_decisions(workflow_decision, decision, deduplicated_rules)
        evaluation = PolicyEvaluation(
            id=decision.evaluation_id,
            project_id=project_id,
            user_story_id=user_story_id,
            gate=gate,
            triggered_rule_ids=decision.triggered_rules,
            result=decision.result,
            missing_evidence=decision.missing_evidence,
            explanation=decision.explanation,
            evaluated_at=datetime.now(UTC).replace(tzinfo=None),
        )
        self.evaluations.save(evaluation)
        self._audit(
            "gate_evaluated",
            project_id,
            str(decision.evaluation_id),
            {
                "user_story_id": str(user_story_id),
                "gate": gate,
                "result": decision.result.value,
                "rule_ids": decision.triggered_rules,
            },
        )
        if decision.result == EvaluationResult.BLOCK:
            self._audit(
                "gate_blocked",
                project_id,
                str(decision.evaluation_id),
                {
                    "user_story_id": str(user_story_id),
                    "gate": gate,
                    "rule_ids": decision.triggered_rules,
                },
            )
        return self._decision_to_dict(decision)

    def register_experience(self, **data: Any) -> EngineeringExperience:
        experience = EngineeringExperience(
            id=uuid4(),
            review_status=ReviewStatus.PENDING,
            created_at=None,
            memory_type=MemoryType(data.pop("memory_type", MemoryType.LESSON_LEARNED)),
            scope=KnowledgeScope(data.pop("scope", KnowledgeScope.PERSONAL)),
            project_id=data.pop("project_id", None),
            related_experience_ids=data.pop("related_experience_ids", []),
            **data,
        )
        if experience.scope == KnowledgeScope.PROJECT and experience.project_id is None:
            raise ApplicationError("Una experiencia PROJECT requiere project_id")
        if experience.project_id is not None:
            self._require_project(experience.project_id)
        return self.experiences.save(experience)

    def review_experience(
        self, experience_id: UUID, status: ReviewStatus, reviewed_by: str
    ) -> EngineeringExperience:
        return self.experiences.save_review(experience_id, status, reviewed_by)

    def register_practice(
        self,
        title: str,
        context: str,
        triggers: dict[str, Any],
        intervention_message: str,
        severity: str,
        scope: KnowledgeScope,
        source_experience_id: UUID | None = None,
        project_id: UUID | None = None,
        owner_id: str | None = None,
        organization_id: str | None = None,
    ) -> EngineeringPractice:
        if scope == KnowledgeScope.PROJECT and project_id is None:
            raise ApplicationError("Una practica PROJECT requiere project_id")
        if scope == KnowledgeScope.PERSONAL and not owner_id:
            raise ApplicationError("Una practica PERSONAL requiere owner_id")
        if scope == KnowledgeScope.ORGANIZATION and not organization_id:
            raise ApplicationError("Una practica ORGANIZATION requiere organization_id")
        if project_id is not None:
            self._require_project(project_id)
        if source_experience_id:
            source = self.experiences.get(source_experience_id)
            if source is None:
                raise ApplicationError("Experiencia de origen no encontrada")
            if source.review_status != ReviewStatus.APPROVED:
                raise ApplicationError("La experiencia de origen debe estar aprobada")
        practice = EngineeringPractice(
            id=uuid4(),
            title=title,
            context=context,
            triggers=triggers,
            intervention_message=intervention_message,
            severity=severity,
            scope=scope,
            source_experience_id=source_experience_id,
            approval_status=ReviewStatus.PENDING,
            project_id=project_id,
            owner_id=owner_id,
            organization_id=organization_id,
        )
        return self.practices.save(practice)

    def list_practices(self, include_unapproved: bool = False) -> list[EngineeringPractice]:
        return self.practices.list(include_unapproved)

    def review_practice(
        self, practice_id: UUID, status: ReviewStatus, reviewed_by: str
    ) -> EngineeringPractice:
        return self.practices.save_review(practice_id, status, reviewed_by)

    def get_applicable_practices(self, context: dict[str, Any]) -> list[EngineeringPractice]:
        self.practice_engine.practices = self.practices.list(include_unapproved=False)
        return self.practice_engine.applicable(context)

    def search_experiences(
        self,
        query: str | None = None,
        component: str | None = None,
        tags: list[str] | None = None,
        include_unreviewed: bool = False,
        project_id: UUID | None = None,
    ) -> list[EngineeringExperience]:
        return self.experience_engine.search(query, component, tags, include_unreviewed, project_id)

    def register_evidence(
        self,
        project_id: UUID,
        user_story_id: UUID,
        policy_id: str,
        evidence_type: str,
        reference: str,
    ) -> Evidence:
        self._require_project(project_id)
        self._require_story(project_id, user_story_id)
        validate_evidence_reference(reference)
        evidence = Evidence(
            id=uuid4(),
            project_id=project_id,
            user_story_id=user_story_id,
            policy_id=policy_id,
            evidence_type=evidence_type,
            reference=reference,
            verification_status=EvidenceStatus.PENDING,
            verified_by=None,
            verified_at=None,
        )
        saved = self.evidences.save(evidence)
        self._audit(
            "evidence_registered",
            project_id,
            str(saved.id),
            {
                "user_story_id": str(user_story_id),
                "policy_id": policy_id,
                "status": saved.verification_status.value,
            },
        )
        return saved

    def verify_evidence(
        self, project_id: UUID, evidence_id: UUID, verified_by: str, approved: bool = True
    ) -> Evidence:
        evidence = self.evidences.get_for_project(project_id, evidence_id)
        if evidence is None:
            raise ApplicationError("Evidencia no encontrada en el proyecto")
        status = EvidenceStatus.VERIFIED if approved else EvidenceStatus.REJECTED
        saved = self.evidences.save(
            replace(
                evidence,
                verification_status=status,
                verified_by=verified_by,
                verified_at=datetime.now(UTC).replace(tzinfo=None),
            )
        )
        self._audit(
            "evidence_status_changed",
            project_id,
            str(evidence.id),
            {
                "user_story_id": str(evidence.user_story_id),
                "policy_id": evidence.policy_id,
                "status": saved.verification_status.value,
            },
        )
        return saved

    def analyze_user_story(self, project_id: UUID, user_story_id: UUID) -> dict[str, Any]:
        story = self._require_story(project_id, user_story_id)
        context = self._story_context(story)
        applicable = self.get_applicable_rules(
            project_id=project_id,
            user_story_id=user_story_id,
            event="development_start",
            stage="development_start",
            changed_files=[],
            context=context,
        )
        issues: list[str] = []
        if not story.description or not story.description.strip():
            issues.append("missing_description")
        if not story.acceptance_criteria:
            issues.append("missing_acceptance_criteria")
        if not context["dependencies_resolved"]:
            issues.append("unresolved_dependencies")
        return {
            "project_id": str(project_id),
            "user_story_id": str(user_story_id),
            "ready_for_development": not issues,
            "issues": issues,
            "applicable_rules": applicable,
        }

    def start_sprint(self, project_id: UUID, sprint_id: UUID | None = None) -> dict[str, Any]:
        self._require_project(project_id)
        stories = self.stories.list_by_project(project_id, sprint_id)
        analyses = [self.analyze_user_story(project_id, story.id) for story in stories]
        return {
            "project_id": str(project_id),
            "sprint_id": str(sprint_id) if sprint_id else None,
            "stories": analyses,
            "total_stories": len(analyses),
            "ready_stories": sum(item["ready_for_development"] for item in analyses),
            "risks": [
                {"user_story_id": item["user_story_id"], "issues": item["issues"]}
                for item in analyses
                if item["issues"]
            ],
        }

    def _require_project(self, project_id: UUID) -> Project:
        project = self.projects.get(project_id)
        if project is None:
            raise ApplicationError("Proyecto no encontrado")
        return project

    def _require_story(self, project_id: UUID, story_id: UUID) -> UserStory:
        story = self.stories.get_for_project(project_id, story_id)
        if story is None:
            raise ApplicationError("Historia no encontrada en el proyecto")
        return story

    @staticmethod
    def _story_context(story: UserStory | None) -> dict[str, Any]:
        if story is None:
            return {
                "description_present": False,
                "acceptance_criteria_present": False,
                "dependencies_resolved": False,
            }
        return {
            "description_present": bool(story.description and story.description.strip()),
            "acceptance_criteria_present": bool(story.acceptance_criteria),
            "dependencies_resolved": all(
                item.get("resolved", item.get("status") in {"DONE", "RESOLVED"})
                for item in story.dependencies
            ),
            "story_status": story.status,
            "story_title": story.title,
        }

    @staticmethod
    def _merge_decisions(workflow: Any, policy: Any, deduplicated_rules: set[str]) -> Any:
        order = {
            EvaluationResult.PASS: 0,
            EvaluationResult.WARN: 1,
            EvaluationResult.BLOCK: 2,
        }
        result = (
            workflow.result if order[workflow.result] >= order[policy.result] else policy.result
        )
        explanations = [
            item
            for item in (
                workflow.explanation if hasattr(workflow, "explanation") else "",
                policy.explanation,
            )
            if item
        ]
        if workflow.errors:
            explanations.append("La evaluacion del workflow contiene errores")
        return replace(
            policy,
            result=result,
            missing_evidence=list(
                dict.fromkeys(workflow.missing_evidence + policy.missing_evidence)
            ),
            explanation=". ".join(dict.fromkeys(explanations)),
            pending_evidence=workflow.pending_evidence,
            rejected_evidence=workflow.rejected_evidence,
            not_applicable_checks=workflow.not_applicable_checks,
            workflow_findings=workflow.findings,
            evaluation_errors=workflow.errors,
            deduplicated_policy_rules=sorted(deduplicated_rules),
        )

    def _audit(
        self,
        event_type: str,
        project_id: UUID,
        entity_id: str | None,
        details: dict[str, Any],
    ) -> None:
        self.audits.save(AuditEntry(event_type, project_id, entity_id, details))

    @staticmethod
    def _infer_event(gate: str, changed_files: list[str]) -> str:
        if gate == "development_start":
            return "development_start"
        if changed_files:
            return "file_change"
        return gate

    @staticmethod
    def _policy_to_dict(policy: Any) -> dict[str, Any]:
        return {
            "id": policy.id,
            "name": policy.name,
            "description": policy.description,
            "version": policy.version,
            "severity": policy.severity,
            "trigger": policy.trigger,
            "scope": policy.scope,
            "conditions": policy.conditions,
            "required_evidence": policy.required_evidence,
            "target_gate": policy.target_gate,
            "action": policy.action,
            "approval_status": policy.approval_status.value,
            "enabled": policy.enabled,
            "workflow_checks": policy.workflow_checks,
        }

    @staticmethod
    def _decision_to_dict(decision: Any) -> dict[str, Any]:
        return {
            "evaluation_id": str(decision.evaluation_id),
            "result": decision.result.value,
            "gate": decision.gate,
            "triggered_rules": decision.triggered_rules,
            "missing_evidence": decision.missing_evidence,
            "explanation": decision.explanation,
            "evaluated_at": decision.evaluated_at.isoformat() if decision.evaluated_at else None,
            "pending_evidence": decision.pending_evidence,
            "rejected_evidence": decision.rejected_evidence,
            "not_applicable_checks": decision.not_applicable_checks,
            "workflow_findings": decision.workflow_findings,
            "evaluation_errors": decision.evaluation_errors,
            "deduplicated_policy_rules": decision.deduplicated_policy_rules,
        }
