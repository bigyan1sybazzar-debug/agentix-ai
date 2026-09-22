from .models import SystemBlueprintSnapshot

PRODUCTION_BLUEPRINT = {
    "version": "v12.0",
    "architecture_name": "Learnami Unified Agent Design & Self-Automation Ecosystem",
    "consolidated_blocks": [
        {
            "name": "1. Shared Governance Core",
            "components": ["Policy Registry", "Orchestration Rules Engine", "Hierarchy & Roles", "Release Readiness Gates", "Governance Audit Logs", "Privacy Controls"]
        },
        {
            "name": "2. Shared Operational Core",
            "components": ["User Onboarding Engine", "Participation Gating", "Content Creation Assistance", "Automated Moderation", "Reaction Engine", "Notifications"]
        },
        {
            "name": "3. Shared Intelligence Core",
            "components": ["Cross-SFP User Memory", "Identity Resolution Engine", "Vector Memory Retrieval", "Module Telemetry Analytics", "Ecosystem Intelligence"]
        },
        {
            "name": "4. SFP Capability Layer",
            "components": ["CliqueFlicks Creator Helpers", "AppFlicks Taste Librarian", "Content Quality & Dedup Filter", "News/Trailer Curation Bot", "Review Post Media Assistant"]
        },
        {
            "name": "5. Supervisory & Oversight Layer",
            "components": ["User-Facing Admin Agent", "Governance Admin Agent", "Chief of Staff Layer", "Orchestration Reporting Sandbox"]
        }
    ],
    "deployment_zones": {
        "core_zone": "Shared Django Backend / cPanel MySQL DB",
        "vector_zone": "Vector Memory Index / Embedding Pipeline",
        "media_zone": "Media Candidate Asset Inspection & Provenance Storage",
        "admin_zone": "Multi-Persona Executive Dashboard & Admin UI"
    },
    "privacy_data_classes": [
        "cross_site_memory",
        "user_pii",
        "moderation_history",
        "identity_links"
    ]
}


def get_production_blueprint() -> dict:
    """Workbook 12: Returns production architectural blueprint."""
    return PRODUCTION_BLUEPRINT


def create_blueprint_snapshot(snapshot_name: str) -> dict:
    """
    Workbook 12: Creates a system blueprint snapshot in database.
    """
    snapshot = SystemBlueprintSnapshot.objects.create(
        snapshot_name=snapshot_name,
        summary=PRODUCTION_BLUEPRINT
    )
    return {
        "id": snapshot.id,
        "snapshot_name": snapshot.snapshot_name,
        "created_at": snapshot.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": snapshot.summary
    }
