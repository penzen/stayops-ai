from typing import Any


PLAYBOOKS: dict[str, dict[str, Any]] = {
    "heating": {
        "category": "heating",
        "name": "Heating Failure",
        "required_checks": [
            "Determine whether heating is completely unavailable or reduced.",
            "Determine whether the thermostat has power and displays normally.",
            "Check for gas smell, smoke, burning smell, major leaking, sparks, or exposed electrical components.",
        ],
        "guest_safe_actions": [
            "Guest may adjust normal thermostat controls.",
        ],
        "prohibited_guest_actions": [
            "Do not instruct the guest to open or dismantle the boiler.",
            "Do not instruct the guest to open electrical panels.",
            "Do not instruct the guest to repair heating equipment.",
        ],
        "operational_actions": {
            "heating_unavailable": [
                "Create or reuse a heating operations task.",
                (
                    "When the guest reports that heating has stopped "
                    "working or is completely unavailable, create or reuse "
                    "a high-priority human escalation immediately."
                ),
                (
                    "Do not delay the human escalation while waiting for "
                    "safe thermostat-level diagnostic answers."
                ),
                (
                    "Diagnostic questions may be asked in parallel with "
                    "the human handoff."
                ),
            ],
        },
        "high_priority_conditions": [
            "No functioning heating.",
            "Conditions make the property unsafe or unsuitable.",
            "Vulnerable guests may be affected.",
            "The failure is worsening.",
            "The guest cannot reasonably remain comfortable.",
        ],
        "resolution_conditions": [
            "Heating has been restored.",
            "A safe temporary alternative has been provided.",
            "The guest has been relocated when the property is unsuitable for continued occupation.",
        ],
    },

    "plumbing": {
        "category": "plumbing",
        "name": "Plumbing Incident",
        "required_checks": [
            "Determine whether water is actively leaking or spreading.",
            "Determine whether the leak is worsening.",
            "Determine whether water is approaching electrical outlets, appliances, or equipment.",
            "Determine whether a bathroom or kitchen is becoming unusable.",
        ],
        "guest_safe_actions": [
            "Ask the guest to stop using the affected fixture.",
            "If safe and obvious, the guest may close the local shutoff valve.",
            "Keep electrical equipment and appliances away from water.",
            "If water approaches electrical outlets or equipment, the guest should leave the affected area.",
        ],
        "prohibited_guest_actions": [
            "Do not instruct the guest to dismantle plumbing fixtures.",
            "Do not expose the guest to areas where water is contacting electrical equipment.",
            "Do not claim maintenance has been dispatched unless an operational tool confirms it.",
        ],
        "operational_actions": {
            "active_water_leak": [
                "Create or reuse a plumbing operations task.",
                "Escalate a worsening or uncontrolled leak with high priority.",
            ],
            "minor_plumbing_issue": [
                "Create or reuse a plumbing operations task.",
                "Escalation priority may remain medium unless the condition is worsening or affecting habitability.",
            ],
        },
        "high_priority_conditions": [
            "Water is actively spreading.",
            "The leak is worsening.",
            "Water may reach electrical equipment.",
            "Significant property damage may occur.",
            "A usable bathroom or kitchen is becoming unavailable.",
        ],
        "critical_conditions": [
            "Water is contacting live electrical equipment.",
            "Flooding creates immediate danger.",
            "Structural damage appears possible.",
        ],
        "resolution_conditions": [
            "The leak has stopped or been contained.",
            "Required repair work has been completed.",
            "The property is safe for continued guest use.",
        ],
    },

    "refund": {
        "category": "refund",
        "name": "Refund and Compensation",
        "required_checks": [
            "Confirm the guest and reservation.",
            "Identify the operational issue connected to the request.",
            "Review relevant incidents, tasks, and operational context.",
            "Determine whether the issue has been documented.",
            "Capture the reason for the request, severity, duration when known, actions already taken, and the guest's requested outcome.",
        ],
        "guest_safe_actions": [
            "Explain that the compensation request can be submitted for human review.",
        ],
        "prohibited_guest_actions": [
            "Do not promise that a refund will be issued.",
            "Do not promise a specific amount.",
            "Do not state that compensation has been approved.",
            "Do not alter payment or booking financial records.",
            "Do not invent a refund percentage or company policy.",
            "Do not calculate or approve final compensation.",
        ],
        "operational_actions": {
            "compensation_request": [
                "Create or reuse a refund-category human escalation.",
                "Tell the guest the request has been submitted for review only after the escalation tool confirms that the escalation exists.",
            ],
        },
        "approval_rules": [
            "Financial decisions require human approval.",
            "The Guest Operations Agent may gather information, explain the review process, and escalate the request.",
        ],
        "resolution_conditions": [
            "An authorized human operator has made and recorded a decision.",
        ],
    },
}


def get_playbook(category: str):
    return PLAYBOOKS.get(
        category.strip().lower()
    )