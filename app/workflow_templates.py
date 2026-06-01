from __future__ import annotations

WORKFLOW_TEMPLATES = [
    {
        "id": "email-summary-slack",
        "name": "Email Summary to Slack",
        "description": "Summarize incoming emails with AI and post the result into Slack.",
        "category": "email",
        "difficulty": "easy",
        "integrations": ["email", "slack"],
        "workflow": {
            "name": "Email Summary to Slack",
            "nodes": [
                {
                    "id": "trigger-1",
                    "type": "triggerNode",
                    "position": {"x": 40, "y": 220},
                    "data": {
                        "label": "Incoming Email",
                        "kind": "trigger",
                        "subtype": "email.received",
                        "config": {"inbox": "primary"},
                    },
                },
                {
                    "id": "action-1",
                    "type": "actionNode",
                    "position": {"x": 360, "y": 140},
                    "data": {
                        "label": "Summarize with AI",
                        "kind": "action",
                        "subtype": "ai.analyze",
                        "config": {"goal": "Summarize email and detect urgency"},
                    },
                },
                {
                    "id": "action-2",
                    "type": "actionNode",
                    "position": {"x": 700, "y": 140},
                    "data": {
                        "label": "Send to Slack",
                        "kind": "action",
                        "subtype": "slack.send",
                        "config": {"channel": "#alerts"},
                    },
                },
            ],
            "edges": [
                {"id": "e1", "source": "trigger-1", "target": "action-1"},
                {"id": "e2", "source": "action-1", "target": "action-2"},
            ],
            "config": {
                "schemaVersion": 1,
                "name": "Email Summary to Slack",
                "trigger": {
                    "type": "email.received",
                    "label": "Incoming Email",
                    "config": {"inbox": "primary"},
                },
                "steps": [
                    {
                        "id": "action-1",
                        "order": 1,
                        "type": "ai.analyze",
                        "label": "Summarize with AI",
                        "config": {"goal": "Summarize email and detect urgency"},
                    },
                    {
                        "id": "action-2",
                        "order": 2,
                        "type": "slack.send",
                        "label": "Send to Slack",
                        "config": {"channel": "#alerts"},
                    },
                ],
                "edges": [
                    {"id": "e1", "source": "trigger-1", "sourceHandle": None, "target": "action-1"},
                    {"id": "e2", "source": "action-1", "sourceHandle": None, "target": "action-2"},
                ],
            },
        },
    },
    {
        "id": "daily-ai-brief",
        "name": "Daily AI Brief",
        "description": "Run on a schedule, create a short brief, and prepare an email delivery.",
        "category": "productivity",
        "difficulty": "easy",
        "integrations": ["email", "schedules"],
        "workflow": {
            "name": "Daily AI Brief",
            "nodes": [
                {
                    "id": "trigger-1",
                    "type": "triggerNode",
                    "position": {"x": 40, "y": 220},
                    "data": {
                        "label": "Daily Schedule",
                        "kind": "trigger",
                        "subtype": "schedule.tick",
                        "config": {"cron": "0 9 * * *"},
                    },
                },
                {
                    "id": "action-1",
                    "type": "actionNode",
                    "position": {"x": 360, "y": 140},
                    "data": {
                        "label": "Generate Brief",
                        "kind": "action",
                        "subtype": "ai.analyze",
                        "config": {"goal": "Create a short daily brief"},
                    },
                },
                {
                    "id": "action-2",
                    "type": "actionNode",
                    "position": {"x": 700, "y": 140},
                    "data": {
                        "label": "Send Email",
                        "kind": "action",
                        "subtype": "email.send",
                        "config": {"to": "user@example.com", "subject": "Daily Brief"},
                    },
                },
            ],
            "edges": [
                {"id": "e1", "source": "trigger-1", "target": "action-1"},
                {"id": "e2", "source": "action-1", "target": "action-2"},
            ],
            "config": {
                "schemaVersion": 1,
                "name": "Daily AI Brief",
                "trigger": {
                    "type": "schedule.tick",
                    "label": "Daily Schedule",
                    "config": {"cron": "0 9 * * *"},
                },
                "steps": [
                    {
                        "id": "action-1",
                        "order": 1,
                        "type": "ai.analyze",
                        "label": "Generate Brief",
                        "config": {"goal": "Create a short daily brief"},
                    },
                    {
                        "id": "action-2",
                        "order": 2,
                        "type": "email.send",
                        "label": "Send Email",
                        "config": {"to": "user@example.com", "subject": "Daily Brief"},
                    },
                ],
                "edges": [
                    {"id": "e1", "source": "trigger-1", "sourceHandle": None, "target": "action-1"},
                    {"id": "e2", "source": "action-1", "sourceHandle": None, "target": "action-2"},
                ],
            },
        },
    },
    {
        "id": "webhook-summary-slack-safe",
        "name": "Webhook Summary to Slack (Safe Mode)",
        "description": "Receive webhook payloads, summarize them, and prepare a safe Slack alert without sending live.",
        "category": "api",
        "difficulty": "medium",
        "integrations": ["api", "slack"],
        "workflow": {
            "name": "Webhook Summary to Slack (Safe Mode)",
            "nodes": [
                {
                    "id": "trigger-1",
                    "type": "triggerNode",
                    "position": {"x": 40, "y": 220},
                    "data": {
                        "label": "Incoming Webhook",
                        "kind": "trigger",
                        "subtype": "webhook.received",
                        "config": {"source": "partner-system", "secret": "smoke-secret"},
                    },
                },
                {
                    "id": "action-1",
                    "type": "actionNode",
                    "position": {"x": 360, "y": 140},
                    "data": {
                        "label": "Summarize Event",
                        "kind": "action",
                        "subtype": "ai.analyze",
                        "config": {"goal": "Summarize the webhook event and surface urgent signals", "mode": "fake"},
                    },
                },
                {
                    "id": "action-2",
                    "type": "actionNode",
                    "position": {"x": 700, "y": 140},
                    "data": {
                        "label": "Prepare Slack Alert",
                        "kind": "action",
                        "subtype": "slack.send",
                        "config": {
                            "channel": "#alerts",
                            "deliveryMode": "fake",
                            "simulateDelayMs": "12000",
                        },
                    },
                },
            ],
            "edges": [
                {"id": "e1", "source": "trigger-1", "target": "action-1"},
                {"id": "e2", "source": "action-1", "target": "action-2"},
            ],
            "config": {
                "schemaVersion": 1,
                "name": "Webhook Summary to Slack (Safe Mode)",
                "trigger": {
                    "type": "webhook.received",
                    "label": "Incoming Webhook",
                    "config": {"source": "partner-system", "secret": "smoke-secret"},
                },
                "steps": [
                    {
                        "id": "action-1",
                        "order": 1,
                        "type": "ai.analyze",
                        "label": "Summarize Event",
                        "config": {"goal": "Summarize the webhook event and surface urgent signals", "mode": "fake"},
                    },
                    {
                        "id": "action-2",
                        "order": 2,
                        "type": "slack.send",
                        "label": "Prepare Slack Alert",
                        "config": {
                            "channel": "#alerts",
                            "deliveryMode": "fake",
                            "simulateDelayMs": "12000",
                        },
                    },
                ],
                "edges": [
                    {"id": "e1", "source": "trigger-1", "sourceHandle": None, "target": "action-1"},
                    {"id": "e2", "source": "action-1", "sourceHandle": None, "target": "action-2"},
                ],
            },
        },
    },
]


def get_workflow_template(template_id: str) -> dict | None:
    for template in WORKFLOW_TEMPLATES:
        if template["id"] == template_id:
            return template
    return None
