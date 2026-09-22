from .models import IdentityCandidateLink


def score_identity_candidate(email_match=False, name_match=False, phone_match=False, sfp_overlap=False):
    """
    Workbook 11: Exact scoring logic for Identity Candidate linking.
    Calculates weighted confidence score and categorizes candidates.
    """
    score = 0.0
    reasons = []

    if email_match:
        score += 0.55
        reasons.append("email_match")
    if name_match:
        score += 0.20
        reasons.append("name_match")
    if phone_match:
        score += 0.20
        reasons.append("phone_match")
    if sfp_overlap:
        score += 0.10
        reasons.append("sfp_overlap")

    if score > 1.0:
        score = 1.0

    status = "candidate"
    if score >= 0.9:
        status = "high_confidence_candidate"
    elif score >= 0.7:
        status = "review_candidate"

    return {
        "confidence_score": round(score, 2),
        "reasons": reasons,
        "status": status
    }


def create_identity_candidate_record(local_user_key: str, sfp_name: str, candidate_global_user_key: str,
                                     email_match=False, name_match=False, phone_match=False, sfp_overlap=False):
    """
    Create an IdentityCandidateLink using the calculated score.
    """
    scored = score_identity_candidate(email_match, name_match, phone_match, sfp_overlap)
    record = IdentityCandidateLink.objects.create(
        local_user_key=local_user_key,
        sfp_name=sfp_name,
        candidate_global_user_key=candidate_global_user_key,
        confidence_score=scored["confidence_score"],
        link_reason=",".join(scored["reasons"]),
        status=scored["status"]
    )
    return record


def run_automated_identity_batch():
    """
    Self-automation runner for pending candidates:
    Auto-confirms high confidence candidates, reviews medium candidates, logs actions.
    """
    candidates = IdentityCandidateLink.objects.filter(status__in=["candidate", "high_confidence_candidate", "review_candidate"])
    processed_count = 0
    auto_confirmed = 0

    for item in candidates:
        if item.status == "high_confidence_candidate" or item.confidence_score >= 0.90:
            item.status = "confirmed"
            item.reviewed_by = "system_automation_agent"
            item.review_notes = f"Auto-confirmed by Version 11 automation logic (confidence: {item.confidence_score:.2f})"
            item.save()
            auto_confirmed += 1
        processed_count += 1

    return {
        "processed": processed_count,
        "auto_confirmed": auto_confirmed,
        "pending_review": processed_count - auto_confirmed
    }
