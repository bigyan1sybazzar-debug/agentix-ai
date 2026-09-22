import re
from .models import UserOnboardingState, GovernanceAuditLog

# Known Disposable & Spam Domains
DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "sharklasers.com",
    "tempmail.com", "yopmail.com", "10minutemail.com", "dispostable.com",
    "thinhmin.com", "code-gmail.com", "chahcyrans.com", "dmxs8.com", "setxko.com",
    "theking.id", "problemno.shop", "skachat-na-android.com", "igurant1.online",
    "phanmembanhang24h.com"
}

# TLDs heavily abused by spam bots
HIGH_RISK_TLDS = {".shop", ".store", ".online", ".id", ".ru", ".top", ".xyz", ".site", ".win", ".club", ".icu", ".best"}

# Keywords matching casino, gambling, crypto spam, and bot usernames
SPAM_PATTERNS = [
    "casino", "crypto", "viagra", "seo", "backlink", "bot", "1win", "1xbet", "888starz",
    "aviator", "payout", "blockchain", "btc", "withdraw", "free-btc", "skachat", "problemno"
]


def evaluate_registration(username: str, email: str, ip_address: str = "127.0.0.1"):
    """
    Workbook 1: Advanced Bot & Fake Email Evaluation Engine.
    Strictly flags and blocks fake emails, random gibberish usernames, and spam domains.
    """
    risk_score = 0.0
    reasons = []

    uname_lower = username.lower()
    email_lower = email.lower()
    local_part, _, domain = email_lower.partition("@")

    # 1. Disposable / Known Spam Domain check
    if domain in DISPOSABLE_DOMAINS:
        risk_score += 0.85
        reasons.append("disposable_or_spam_domain")

    # 2. High-Risk TLD Check
    for tld in HIGH_RISK_TLDS:
        if domain.endswith(tld):
            risk_score += 0.60
            reasons.append(f"high_risk_tld:{tld}")
            break

    # 3. Fake Gmail Clone Check (e.g. @gmail.ru, @code-gmail.com)
    if "gmail" in domain and domain not in ["gmail.com", "googlemail.com"]:
        risk_score += 0.90
        reasons.append("fake_gmail_domain")

    # 4. Spam Keywords in Username or Email
    for pattern in SPAM_PATTERNS:
        if pattern in uname_lower or pattern in email_lower:
            risk_score += 0.75
            reasons.append(f"spam_keyword:{pattern}")

    # 5. Gibberish / Bot Username Detector (e.g., 0thz91, 1hfjkf23, 4k21jr, 5pljks, 78gt4s)
    # High proportion of digits + random consonants
    if re.search(r'^[0-9]+[a-z0-9]{4,}$', uname_lower) or re.search(r'^[a-z0-9]{6,}$', uname_lower):
        # Count vowels vs consonants in username
        letters = re.sub(r'[^a-z]', '', uname_lower)
        if letters:
            vowel_count = len(re.findall(r'[aeiou]', letters))
            vowel_ratio = vowel_count / len(letters)
            if vowel_ratio < 0.15 and len(letters) >= 5:
                risk_score += 0.65
                reasons.append("gibberish_username_pattern")

    # 6. Numeric-Only or Short Username Check
    if username.isdigit():
        risk_score += 0.50
        reasons.append("numeric_only_username")

    if len(username) < 3 or len(username) > 30:
        risk_score += 0.20
        reasons.append("abnormal_username_length")

    # Cap risk score at 1.0
    risk_score = min(1.0, risk_score)

    # Classification & Action Logic
    if risk_score >= 0.60:
        status = "rejected"
        role = "restricted_blocked"
        stage = "escalated"
    elif risk_score >= 0.30:
        status = "flagged"
        role = "subscriber_probationary"
        stage = "escalated"
    else:
        status = "approved"
        role = "subscriber_probationary"
        stage = "email_pending"

    return {
        "evaluation_status": status,
        "risk_score": round(risk_score, 2),
        "risk_reasons": ",".join(reasons) if reasons else "clean",
        "assigned_role": role,
        "onboarding_stage": stage,
        "can_post": False,
        "can_comment": False,
        "can_vote": False
    }


def evaluate_role_progression(user_state: UserOnboardingState):
    """
    Workbook 2: Progressive Profiling & Access Control Engine.
    Only allows progression if risk score is clean (<0.30) and email is verified.
    """
    changes = []

    # Blocked or high risk users can NEVER progress
    if user_state.risk_score >= 0.60 or user_state.evaluation_status == "rejected":
        user_state.assigned_role = "restricted_blocked"
        user_state.can_post = False
        user_state.can_comment = False
        user_state.can_vote = False
        user_state.save()
        return ["blocked_high_risk"]

    if user_state.email_verified:
        if user_state.onboarding_stage == "email_pending":
            user_state.onboarding_stage = "progressive_asks"
            changes.append("email_verified")

        has_age = bool(user_state.age and user_state.age >= 13)
        has_loc = bool(user_state.location)
        has_bio = bool(user_state.bio and len(user_state.bio.strip()) >= 10)

        if has_age and has_loc and has_bio:
            user_state.onboarding_stage = "completed"
            user_state.assigned_role = "subscriber_trusted"
            user_state.can_comment = True
            user_state.can_post = True
            user_state.can_vote = True
            changes.append("promoted_to_trusted")
        elif has_age:
            user_state.can_comment = True
            changes.append("unlocked_comments")

    user_state.save()
    return changes


def run_automated_onboarding_batch():
    """
    Self-automation runner for Onboarding Layer (v1 & v2).
    Evaluates all user accounts using strict bot & fake email detection.
    """
    all_users = UserOnboardingState.objects.all()
    promoted_count = 0
    evaluated_count = 0

    for u in all_users:
        res = evaluate_registration(u.username, u.email)
        u.evaluation_status = res["evaluation_status"]
        u.risk_score = res["risk_score"]
        u.risk_reasons = res["risk_reasons"]
        u.assigned_role = res["assigned_role"]
        u.onboarding_stage = res["onboarding_stage"]
        u.save()
        evaluated_count += 1

        # Only clean accounts (< 0.30 risk) get progressive promotion
        if u.risk_score < 0.30 and u.email_verified:
            changes = evaluate_role_progression(u)
            if "promoted_to_trusted" in changes:
                promoted_count += 1
                GovernanceAuditLog.objects.create(
                    actor_type="system",
                    actor_id=f"wp_{u.wp_user_id}",
                    event_type="onboarding_progression",
                    action="promote_to_trusted",
                    result="allow",
                    details={"username": u.username, "role": u.assigned_role}
                )

    return {
        "evaluated_count": evaluated_count,
        "promoted_count": promoted_count
    }
