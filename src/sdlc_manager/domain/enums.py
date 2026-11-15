from enum import StrEnum


class EvaluationResult(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    BLOCK = "BLOCK"


class EvidenceStatus(StrEnum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class ReviewStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class PolicyApprovalStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"


class MemoryType(StrEnum):
    INCIDENT = "INCIDENT"
    BUG = "BUG"
    LESSON_LEARNED = "LESSON_LEARNED"
    RECOMMENDATION = "RECOMMENDATION"
    PREFERENCE = "PREFERENCE"
    POLICY = "POLICY"


class KnowledgeScope(StrEnum):
    PERSONAL = "PERSONAL"
    PROJECT = "PROJECT"
    ORGANIZATION = "ORGANIZATION"


class WorkflowStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class SdlcEventType(StrEnum):
    SESSION_STARTED = "session_started"
    SPRINT_STARTED = "sprint_started"
    USER_STORY_STARTED = "user_story_started"
    SDD_TASK_STARTED = "sdd_task_started"
    FILE_CHANGED = "file_changed"
    TASK_COMPLETED = "task_completed"
    GATE_EVALUATION_REQUESTED = "gate_evaluation_requested"
    INCIDENT_RECORDED = "incident_recorded"


class EventProcessingStatus(StrEnum):
    PROCESSED = "PROCESSED"
    DUPLICATE = "DUPLICATE"
    UNSUPPORTED = "UNSUPPORTED"
    REJECTED = "REJECTED"
    ERROR = "ERROR"
