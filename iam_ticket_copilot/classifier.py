"""Deterministic category, priority and assignment suggestions; never a policy decision."""
from __future__ import annotations

import re

from .models import Ticket

# Rule weights are explicit and auditable. The signal is an exact dictionary phrase,
# not a statistical confidence estimate. Category matching is intentionally conservative.
RULES: dict[str, dict[str, int]] = {
    "Offboarding": {
        "offboarding": 5, "offboard": 5, "terminated employee": 5,
        "termination": 4, "departed employee": 5, "leaver": 4,
        "disable departed": 5, "revoke access": 3,
    },
    "Provisioning Failure": {
        "provisioning failed": 6, "provisioning failure": 6,
        "sync failed": 5, "connector error": 5, "scim failure": 5,
        "driver stopped": 5, "netiq driver": 5, "no account created": 4,
    },
    "Account Lockout": {
        "locked out": 6, "account locked": 6, "account lockout": 6,
        "unlock account": 5, "login locked": 5,
    },
    "MFA Support": {
        "mfa": 5, "authenticator": 5, "push notification": 4,
        "verification code": 4, "second factor": 4,
    },
    "Mover / Role Change": {
        "department transfer": 6, "role change": 5,
        "new department": 5, "job transfer": 5, "role mapping": 5,
        "team transfer": 4, "mover": 4,
    },
    "Access Request": {
        "request access": 6, "needs access": 5,
        "access approval": 4, "grant access": 5,
        "permission request": 5, "access request": 5,
    },
    "License / Entitlement": {
        "license": 5, "licence": 5, "unassigned seat": 5,
        "subscription": 4, "entitlement usage": 5,
    },
}

ASSIGNMENTS = {
    "Offboarding": "Identity Lifecycle Operations",
    "Provisioning Failure": "IAM Provisioning Operations",
    "Account Lockout": "Identity Service Desk",
    "MFA Support": "Identity Authentication Support",
    "Mover / Role Change": "Identity Governance Operations",
    "Access Request": "IAM Access Fulfillment",
    "License / Entitlement": "SaaS Access Operations",
    "Needs Analyst Review": "IAM Triage Queue",
}

PLAYBOOKS = {
    "Offboarding": [
        "Confirm the authoritative termination effective time and approved offboarding scope.",
        "Compare account-disable and entitlement-revocation evidence across systems.",
        "Escalate any potentially active post-termination access for human investigation.",
    ],
    "Provisioning Failure": [
        "Review connector status, last successful sync and provisioning error codes.",
        "Correlate the user's source identity record with the target application record.",
        "Check retry queues and change records; obtain approval before any retry.",
    ],
    "Account Lockout": [
        "Verify the requester's identity through approved help-desk procedure.",
        "Review lockout timestamps and upstream authentication event sources.",
        "Follow the documented unlock process only after authorization.",
    ],
    "MFA Support": [
        "Verify identity using the approved recovery process.",
        "Check registered factors, recent challenges and device changes.",
        "Escalate unexpected MFA approvals or push fatigue indicators.",
    ],
    "Mover / Role Change": [
        "Verify the authoritative department/role effective date and manager approvals.",
        "Compare requested entitlements with current group membership and role mappings.",
        "Review mover workflow execution evidence before manual remediation.",
    ],
    "Access Request": [
        "Confirm the application, access scope and business justification.",
        "Verify the approval route and separation-of-duties requirements.",
        "Do not grant access until normal owner and manager approvals complete.",
    ],
    "License / Entitlement": [
        "Verify the license pool, active assignment and subscription owner.",
        "Check entitlement need and approved reclaim/reassign policy.",
        "Obtain approval before changing any license assignment.",
    ],
    "Needs Analyst Review": [
        "Request the affected application, account, error text and timeframe.",
        "Check the supported runbooks and route to the IAM triage queue.",
        "Do not infer entitlements or perform automated changes.",
    ],
}


def _matches(haystack: str, phrase: str) -> bool:
    # Match complete phrases; "down" must not match "download".
    return re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", haystack) is not None


def classify(ticket: Ticket) -> tuple[str, str, list[str]]:
    raw = f"{ticket.subject} {ticket.description}".lower()
    # A single ticket requesting both granting and revoking access should
    # be split or explicitly assessed by a human; never select a queue blindly.
    if _matches(raw, "request access") and _matches(raw, "revoke access"):
        return "Needs Analyst Review", "ambiguous", ["request access", "revoke access"]
    weights: list[tuple[int, str, list[str]]] = []
    for category, patterns in RULES.items():
        hits = [phrase for phrase in patterns if _matches(raw, phrase)]
        if hits:
            weights.append((sum(patterns[h] for h in hits), category, hits))
    if not weights:
        return "Needs Analyst Review", "unmatched", []
    weights.sort(key=lambda x: (-x[0], x[1]))
    winning = weights[0]
    second = weights[1][0] if len(weights) > 1 else 0
    strength = "strong" if winning[0] >= 8 and winning[0] - second >= 3 else "moderate"
    if second >= winning[0] - 1:
        # Competing signals can indicate mixed tickets. Avoid false certainty.
        return "Needs Analyst Review", "ambiguous", sorted(set(winning[2] + weights[1][2]))
    return winning[1], strength, winning[2]


def prioritize(ticket: Ticket, category: str) -> tuple[str, list[str]]:
    raw = f"{ticket.subject} {ticket.description}".lower()
    major = any(_matches(raw, phrase) for phrase in (
        "enterprise-wide", "company-wide", "all employees", "entire company", "global outage",
    ))
    outage = any(_matches(raw, phrase) for phrase in ("outage", "unavailable", "down", "failure", "failed"))
    if major and outage:
        return "P1", ["potential broad service impact", "human validation required"]
    critical = any(_matches(raw, phrase) for phrase in (
        "production outage", "critical", "executive", "multiple users", "security incident",
    ))
    if critical:
        return "P2", ["potential elevated impact", "confirm with incident policy"]
    if category == "Needs Analyst Review":
        return "P3", ["unclear impact; manual assessment required"]
    return "P3", ["default suggestion; verify urgency and impact"]
