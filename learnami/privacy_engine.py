from .models import PrivacyAccessLog, ConsentRecord


def evaluate_privacy_access(requester_role: str, data_class: str, target_key: str = None) -> dict:
    """
    Workbook 12: Evaluates data access based on requester role and target data class.
    Data classes: 'cross_site_memory', 'user_pii', 'moderation_history', 'identity_links'
    """
    allowed_matrix = {
        "user_facing_admin_agent": ["moderation_history", "user_pii"],
        "governance_admin_agent": ["cross_site_memory", "identity_links", "moderation_history"],
        "chief_of_staff": ["cross_site_memory", "user_pii", "moderation_history", "identity_links"],
        "operational_agent": ["moderation_history"],
    }

    allowed_classes = allowed_matrix.get(requester_role, [])
    
    if data_class in allowed_classes:
        decision = "allowed"
        reason = f"Role '{requester_role}' has explicit permission for '{data_class}'."
    elif requester_role == "guest" or not requester_role:
        decision = "denied"
        reason = "Unauthenticated or guest role cannot access internal data classes."
    else:
        decision = "masked"
        reason = f"Role '{requester_role}' lacks full permission for '{data_class}'. Result will be masked/anonymized."

    log_entry = PrivacyAccessLog.objects.create(
        requester_role=requester_role,
        data_class=data_class,
        target_key=target_key,
        decision=decision,
        reason=reason
    )

    return {
        "log_id": log_entry.id,
        "requester_role": requester_role,
        "data_class": data_class,
        "target_key": target_key,
        "decision": decision,
        "reason": reason,
    }


def record_consent(global_user_key: str, consent_type: str, granted: bool, source_sfp: str = None, evidence: dict = None) -> dict:
    """
    Workbook 12: Records or updates user consent for cross-site memory sharing.
    """
    record, created = ConsentRecord.objects.update_or_create(
        global_user_key=global_user_key,
        consent_type=consent_type,
        defaults={
            "granted": granted,
            "source_sfp": source_sfp or "system",
            "evidence": evidence or {}
        }
    )

    return {
        "id": record.id,
        "global_user_key": record.global_user_key,
        "consent_type": record.consent_type,
        "granted": record.granted,
        "source_sfp": record.source_sfp,
        "status": "created" if created else "updated"
    }


def evaluate_cross_site_memory(global_user_key: str, sfp_source: str, sfp_target: str) -> dict:
    """
    Workbook 12: Checks if cross-site memory access between SFPs is permitted based on user consent.
    """
    consent = ConsentRecord.objects.filter(
        global_user_key=global_user_key,
        consent_type="cross_site_memory"
    ).first()

    if consent and consent.granted:
        return {
            "allowed": True,
            "global_user_key": global_user_key,
            "sfp_source": sfp_source,
            "sfp_target": sfp_target,
            "reason": f"Explicit user consent granted for cross-site memory between {sfp_source} and {sfp_target}."
        }

    return {
        "allowed": False,
        "global_user_key": global_user_key,
        "sfp_source": sfp_source,
        "sfp_target": sfp_target,
        "reason": f"User consent for cross-site memory not found or set to denied. Defaulting to strict isolation."
    }
