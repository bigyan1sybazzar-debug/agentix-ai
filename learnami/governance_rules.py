from .models import GovernanceAuditLog, UserOnboardingState


def evaluate_governance_context(wp_user_id: int, action: str, platform_context: str = "general"):
    """
    Workbook 4: Governance Reasoning Engine.
    Checks multi-context permissions (age, location, role restrictions).
    """
    user = UserOnboardingState.objects.filter(wp_user_id=wp_user_id).first()
    if not user:
        return {"allowed": False, "reason": "User record not found in governance store."}

    # 1. Location restriction (e.g. VotersForTruth political forum scenario)
    if platform_context == "voters_for_truth":
        if user.location and user.location.upper() not in ["US", "USA", "UNITED STATES"]:
            return {
                "allowed": False,
                "reason": f"Platform '{platform_context}' restricts posting to US residents. User location: '{user.location}'."
            }

    # 2. Age compliance
    if user.age and user.age < 13:
        return {"allowed": False, "reason": "Underage user (under 13). Action blocked per COPPA compliance."}

    # 3. Role capability
    if action == "publish_post" and not user.can_post:
        return {"allowed": False, "reason": f"Role '{user.assigned_role}' lacks 'can_post' capability."}

    if action == "comment" and not user.can_comment:
        return {"allowed": False, "reason": f"Role '{user.assigned_role}' lacks 'can_comment' capability."}

    return {"allowed": True, "reason": "Action approved by governance rules engine."}


def validate_profile_readiness(user_state: UserOnboardingState):
    """
    Workbook 4: Validation Rule for profile readiness.
    """
    missing = []
    if not user_state.email_verified:
        missing.append("email_verification")
    if not user_state.age:
        missing.append("age")
    if not user_state.location:
        missing.append("location")
    if not user_state.bio:
        missing.append("bio")

    score = 100 - (len(missing) * 25)
    return {
        "readiness_score": score,
        "is_ready": (len(missing) == 0),
        "missing_fields": missing
    }


def evaluate_reactions(event_type: str, payload: dict):
    """
    Workbook 4: Reaction Rules Engine.
    Automated system reactions triggered when events happen across the ecosystem.
    """
    reactions = []

    if event_type == "moderation_rejected":
        reactions.append({
            "reaction": "send_moderation_warning",
            "target_user": payload.get("wp_user_id"),
            "channel": "system_notification",
            "message": "Your submission was rejected by moderation due to policy violation."
        })
        reactions.append({
            "reaction": "demote_probationary",
            "target_user": payload.get("wp_user_id")
        })

    elif event_type == "high_risk_registration":
        reactions.append({
            "reaction": "lock_probationary_account",
            "target_user": payload.get("wp_user_id"),
            "reason": "Automated security lockdown: Disposable domain or spam keywords detected."
        })
        reactions.append({
            "reaction": "escalate_to_admin_queue",
            "priority": "urgent"
        })

    elif event_type == "profile_completed":
        reactions.append({
            "reaction": "unlock_full_membership",
            "target_user": payload.get("wp_user_id")
        })
        reactions.append({
            "reaction": "grant_verified_badge",
            "badge_name": "Trusted Pioneer"
        })

    # Record reactions in audit log
    for r in reactions:
        GovernanceAuditLog.objects.create(
            actor_type="system",
            actor_id=str(payload.get("wp_user_id", "system")),
            event_type=f"reaction_fired:{r['reaction']}",
            action=event_type,
            result="applied",
            details=r
        )

    return reactions
