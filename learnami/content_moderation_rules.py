from .models import ContentSubmission, ModerationCase, UserOnboardingState, GovernanceAuditLog

MODERATION_REASON_CODES = {
    "SPAM": "Content detected as commercial, promotional, or repetitive spam.",
    "HARASSMENT": "Content contains hostile or aggressive language.",
    "POLICY_VIOLATION": "Breaches community editorial guidelines.",
    "UNVERIFIED_AUTHOR": "Author has not completed probationary email/onboarding verification.",
    "OFF_TOPIC": "Submission deviates from the designated forum/review category.",
    "LOW_QUALITY": "Content is too brief or lacks meaningful substance."
}

FORBIDDEN_KEYWORDS = ["buy cheap", "free crypto", "wire transfer", "click here now", "viagra", "casino online"]


def evaluate_content_submission(submission_id: int):
    """
    Workbook 3: Content Participation & Moderation Engine.
    Evaluates submitted content against quality, author trust, and keyword filters.
    """
    try:
        sub = ContentSubmission.objects.get(id=submission_id)
    except ContentSubmission.DoesNotExist:
        return None

    flags = []

    # 1. Author trust check
    user = UserOnboardingState.objects.filter(wp_user_id=sub.wp_user_id).first()
    if user and not user.can_post:
        flags.append(("UNVERIFIED_AUTHOR", f"User '{user.username}' is in '{user.assigned_role}' role and lacks posting permissions."))

    # 2. Length check
    if len(sub.title.strip()) < 5:
        flags.append(("LOW_QUALITY", "Title is shorter than 5 characters."))
    if len(sub.body.strip()) < 20:
        flags.append(("LOW_QUALITY", "Body content is too brief (minimum 20 characters)."))

    # 3. Keyword check
    body_lower = sub.body.lower()
    for kw in FORBIDDEN_KEYWORDS:
        if kw in body_lower:
            flags.append(("SPAM", f"Detected restricted keyword: '{kw}'"))
            break

    # Decision
    if flags:
        sub.status = "flagged"
        sub.save()
        
        # Create moderation cases for each flag
        for code, reason in flags:
            ModerationCase.objects.create(
                submission=sub,
                wp_user_id=sub.wp_user_id,
                reason_code=code,
                flagged_reason=reason,
                status="open"
            )

        GovernanceAuditLog.objects.create(
            actor_type="system",
            actor_id=f"wp_{sub.wp_user_id}",
            event_type="content_moderation",
            action="flag_submission",
            result="flag",
            details={"title": sub.title, "flags": [f[0] for f in flags]}
        )
    else:
        sub.status = "approved"
        sub.save()
        GovernanceAuditLog.objects.create(
            actor_type="system",
            actor_id=f"wp_{sub.wp_user_id}",
            event_type="content_moderation",
            action="auto_approve_submission",
            result="allow",
            details={"title": sub.title}
        )

    return sub


def run_automated_moderation_batch():
    """
    Self-automation runner for content moderation (v3).
    Processes all pending submissions.
    """
    pending = ContentSubmission.objects.filter(status="submitted")
    count = 0
    approved = 0
    flagged = 0

    for sub in pending:
        evaluated = evaluate_content_submission(sub.id)
        if evaluated.status == "approved":
            approved += 1
        elif evaluated.status == "flagged":
            flagged += 1
        count += 1

    return {
        "processed_count": count,
        "approved_count": approved,
        "flagged_count": flagged
    }


