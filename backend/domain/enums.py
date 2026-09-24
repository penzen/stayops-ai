from enum import StrEnum


class IssueCategory(StrEnum):
    ACCESS = "access"
    PLUMBING = "plumbing"
    HEATING = "heating"
    ELECTRICAL = "electrical"
    MAINTENANCE = "maintenance"
    SAFETY = "safety"
    CLEANING = "cleaning"
    WIFI = "wifi"
    REFUND = "refund"
    OTHER = "other"


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CaseStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"


class SenderType(StrEnum):
    GUEST = "guest"
    AGENT = "agent"
    HUMAN = "human"