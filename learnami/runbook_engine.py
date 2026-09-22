from django.utils import timezone
from .models import RunbookExecution

RUNBOOK_DEFINITIONS = {
    "policy_error_detected": {
        "title": "Policy Error Detected Runbook",
        "description": "Triggered when policy execution throws exceptions or contradictory rules are found.",
        "steps": [
            "1. Quarantining faulty policy rule.",
            "2. Reverting to prior verified policy snapshot.",
            "3. Dispatching notification to Governance Admin Agent.",
            "4. Generating policy impact simulation diagnostic."
        ]
    },
    "moderation_surge": {
        "title": "Moderation Queue Surge Runbook",
        "description": "Triggered when unreviewed moderation queue exceeds baseline volume threshold.",
        "steps": [
            "1. Escalating automated filtering sensitivity.",
            "2. Auto-pausing high-risk unverified candidate posts.",
            "3. Alerting User-Facing Admin Agent for batch review.",
            "4. Logging queue telemetry snapshot."
        ]
    },
    "queue_backup": {
        "title": "Pipeline Event Queue Backup Runbook",
        "description": "Triggered when asynchronous task queue latency exceeds SLA limit.",
        "steps": [
            "1. Scaling active worker instances.",
            "2. Deprioritizing low-priority telemetry snapshots.",
            "3. Re-enqueuing stalled task batches."
        ]
    },
    "outage_recovery": {
        "title": "Outage & Self-Healing Restoration Runbook",
        "description": "Triggered during database or external service failover.",
        "steps": [
            "1. Verifying database connection pool status.",
            "2. Performing auto-migration check.",
            "3. Re-indexing vector memory cache.",
            "4. Emitting Chief of Staff system status health check."
        ]
    }
}


def list_runbooks() -> list:
    """Returns catalog of defined operational runbooks."""
    return [
        {
            "key": key,
            "title": data["title"],
            "description": data["description"],
            "step_count": len(data["steps"]),
            "steps": data["steps"]
        }
        for key, data in RUNBOOK_DEFINITIONS.items()
    ]


def start_runbook_execution(runbook_key: str, triggered_by: str = None, notes: str = None) -> dict:
    """
    Workbook 12: Starts operational runbook execution and logs steps.
    """
    definition = RUNBOOK_DEFINITIONS.get(runbook_key)
    if not definition:
        return {"error": f"Runbook key '{runbook_key}' not found."}

    execution = RunbookExecution.objects.create(
        runbook_key=runbook_key,
        triggered_by=triggered_by or "system_automation",
        status="running",
        notes=notes or f"Initiated {definition['title']}",
        steps_completed=[f"INIT: {definition['steps'][0]}"]
    )

    return {
        "execution_id": execution.id,
        "runbook_key": execution.runbook_key,
        "triggered_by": execution.triggered_by,
        "status": execution.status,
        "steps_completed": execution.steps_completed,
        "created_at": execution.created_at.strftime("%Y-%m-%d %H:%M:%S")
    }


def complete_runbook_execution(execution_id: int, notes: str = None) -> dict:
    """
    Workbook 12: Completes runbook execution.
    """
    try:
        execution = RunbookExecution.objects.get(id=execution_id)
    except RunbookExecution.DoesNotExist:
        return {"error": f"Runbook execution #{execution_id} not found."}

    definition = RUNBOOK_DEFINITIONS.get(execution.runbook_key, {})
    all_steps = definition.get("steps", [])

    execution.status = "completed"
    execution.steps_completed = all_steps
    execution.notes = notes or "Runbook execution finished successfully."
    execution.completed_at = timezone.now()
    execution.save()

    return {
        "execution_id": execution.id,
        "runbook_key": execution.runbook_key,
        "status": execution.status,
        "steps_completed": execution.steps_completed,
        "completed_at": execution.completed_at.strftime("%Y-%m-%d %H:%M:%S")
    }
