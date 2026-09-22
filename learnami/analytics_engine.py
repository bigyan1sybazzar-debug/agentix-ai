from .models import ModuleAnalyticsSnapshot, IdentityCandidateLink, MediaCandidate, RetrievalDocument


def summarize_module_activity(module_key: str, usage_count: int, approval_count: int, rejection_count: int, escalation_count: int):
    """
    Workbook 11: Exact function from agent-api/app/analytics_engine.py
    """
    return {
        "module_key": module_key,
        "usage_count": usage_count,
        "approval_count": approval_count,
        "rejection_count": rejection_count,
        "escalation_count": escalation_count,
        "approval_rate": (approval_count / usage_count) if usage_count else 0.0,
        "escalation_rate": (escalation_count / usage_count) if usage_count else 0.0
    }


def create_module_analytics_snapshot(module_key: str, sfp_name: str, usage_count: int, approval_count: int,
                                     rejection_count: int, escalation_count: int, notes: dict | None = None):
    """
    Workbook 11: Creates and persists a ModuleAnalyticsSnapshot.
    """
    summary = summarize_module_activity(module_key, usage_count, approval_count, rejection_count, escalation_count)
    snapshot = ModuleAnalyticsSnapshot.objects.create(
        module_key=module_key,
        sfp_name=sfp_name,
        usage_count=usage_count,
        approval_count=approval_count,
        rejection_count=rejection_count,
        escalation_count=escalation_count,
        notes=notes or summary
    )
    return snapshot


def run_automated_analytics_telemetry():
    """
    Self-automation runner:
    Inspects live system statistics and auto-generates analytics snapshots for each active module.
    """
    snapshots_created = []

    # 1. Identity Resolution Telemetry
    total_identities = IdentityCandidateLink.objects.count()
    approved_identities = IdentityCandidateLink.objects.filter(status="confirmed").count()
    rejected_identities = IdentityCandidateLink.objects.filter(status="rejected").count()
    escalated_identities = IdentityCandidateLink.objects.filter(status="review_candidate").count()

    snap_id = create_module_analytics_snapshot(
        module_key="identity_resolution",
        sfp_name="sfp_user_graph",
        usage_count=total_identities,
        approval_count=approved_identities,
        rejection_count=rejected_identities,
        escalation_count=escalated_identities,
        notes={"telemetry_source": "automated_db_audit"}
    )
    snapshots_created.append(snap_id)

    # 2. Media Assistant Telemetry
    total_media = MediaCandidate.objects.count()
    approved_media = MediaCandidate.objects.filter(validation_status="approved").count()
    rejected_media = MediaCandidate.objects.filter(validation_status="rejected").count()
    escalated_media = MediaCandidate.objects.filter(validation_status="review_required").count()

    snap_media = create_module_analytics_snapshot(
        module_key="media_assistant",
        sfp_name="sfp_review_posts",
        usage_count=total_media,
        approval_count=approved_media,
        rejection_count=rejected_media,
        escalation_count=escalated_media,
        notes={"telemetry_source": "automated_db_audit"}
    )
    snapshots_created.append(snap_media)

    # 3. Vector Retrieval Telemetry
    total_docs = RetrievalDocument.objects.count()
    embedded_docs = RetrievalDocument.objects.filter(vector_status="embedded").count()
    failed_docs = RetrievalDocument.objects.filter(vector_status="failed").count()
    pending_docs = RetrievalDocument.objects.filter(vector_status="pending").count()

    snap_retrieval = create_module_analytics_snapshot(
        module_key="retrieval_engine",
        sfp_name="sfp_knowledge_base",
        usage_count=total_docs,
        approval_count=embedded_docs,
        rejection_count=failed_docs,
        escalation_count=pending_docs,
        notes={"telemetry_source": "automated_db_audit"}
    )
    snapshots_created.append(snap_retrieval)

    return {
        "snapshots_count": len(snapshots_created),
        "modules": ["identity_resolution", "media_assistant", "retrieval_engine"]
    }
