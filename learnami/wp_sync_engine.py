"""
WordPress Live Sync Engine
Reads real data from WordPress MySQL tables (8uI_ prefix) and syncs into Learnami governance tables.
Handles: Users → OnboardingState, Posts/Comments → ContentSubmission
"""
from django.db import connection
from .models import UserOnboardingState, ContentSubmission, GovernanceAuditLog
from .registration_rules import evaluate_registration, evaluate_role_progression

# WordPress table prefix on this Bluehost install
WP_PREFIX = "8uI_"

# Map WP roles to Learnami roles
WP_ROLE_MAP = {
    "administrator": "subscriber_trusted",
    "editor": "subscriber_trusted",
    "author": "subscriber_trusted",
    "appflicker_critic": "subscriber_trusted",
    "joulepepper_contributor": "subscriber_trusted",
    "cinetaste_contributor": "subscriber_trusted",
    "fmwp_participant": "subscriber_trusted",
    "bbp_participant": "subscriber_probationary",
    "bbp_spectator": "subscriber_probationary",
    "contributor": "subscriber_probationary",
    "subscriber": "subscriber_probationary",
}

# Roles considered "trusted" — can post, comment, vote
TRUSTED_ROLES = {
    "administrator", "editor", "author",
    "appflicker_critic", "joulepepper_contributor",
    "cinetaste_contributor", "fmwp_participant",
}


def parse_wp_capabilities(meta_value: str) -> list:
    """
    Parse WordPress serialized PHP capability string.
    e.g. 'a:1:{s:17:"appflicker_critic";b:1;}' → ['appflicker_critic']
    Simple regex-based extractor (no PHP needed).
    """
    import re
    roles = re.findall(r'"([^"]+)";b:1', meta_value or "")
    return roles


def get_wp_users_with_roles(limit=500):
    """
    Fetch real WP users with their roles from 8uI_users + 8uI_usermeta.
    Returns list of dicts.
    """
    sql = f"""
        SELECT 
            u.ID, u.user_login, u.user_email, u.display_name,
            u.user_registered, u.user_status,
            um.meta_value as capabilities_raw
        FROM `{WP_PREFIX}users` u
        LEFT JOIN `{WP_PREFIX}usermeta` um 
            ON u.ID = um.user_id 
            AND um.meta_key = '{WP_PREFIX}capabilities'
        ORDER BY u.ID ASC
        LIMIT {limit}
    """
    with connection.cursor() as c:
        c.execute(sql)
        cols = [col[0] for col in c.description]
        return [dict(zip(cols, row)) for row in c.fetchall()]


def get_wp_posts_for_moderation(limit=200):
    """
    Fetch real WP posts (reviews, forum posts) for moderation sync.
    Returns list of dicts.
    """
    sql = f"""
        SELECT 
            p.ID, p.post_author, p.post_title, p.post_content,
            p.post_type, p.post_status, p.post_date,
            u.user_login
        FROM `{WP_PREFIX}posts` p
        LEFT JOIN `{WP_PREFIX}users` u ON p.post_author = u.ID
        WHERE p.post_status IN ('publish', 'pending', 'draft')
          AND p.post_type IN ('post', 'review', 'forum', 'topic')
          AND p.post_title != ''
        ORDER BY p.post_date DESC
        LIMIT {limit}
    """
    with connection.cursor() as c:
        c.execute(sql)
        cols = [col[0] for col in c.description]
        return [dict(zip(cols, row)) for row in c.fetchall()]


def get_wp_comments_for_moderation(limit=200):
    """
    Fetch recent WP comments for moderation sync.
    """
    sql = f"""
        SELECT 
            c.comment_ID, c.user_id, c.comment_author,
            c.comment_author_email, c.comment_content,
            c.comment_date, c.comment_approved,
            p.post_title as post_title
        FROM `{WP_PREFIX}comments` c
        LEFT JOIN `{WP_PREFIX}posts` p ON c.comment_post_ID = p.ID
        WHERE c.comment_type IN ('', 'comment')
        ORDER BY c.comment_date DESC
        LIMIT {limit}
    """
    with connection.cursor() as c:
        c.execute(sql)
        cols = [col[0] for col in c.description]
        return [dict(zip(cols, row)) for row in c.fetchall()]


def sync_wp_users_to_onboarding(limit=500):
    """
    Main sync function: reads WP users and upserts into UserOnboardingState.
    Assigns correct Learnami roles based on WP roles.
    Returns summary dict.
    """
    wp_users = get_wp_users_with_roles(limit=limit)
    created = 0
    updated = 0
    trusted = 0
    blocked = 0

    for wp in wp_users:
        wp_id = wp["ID"]
        username = wp["user_login"] or ""
        email = wp["user_email"] or ""
        display_name = wp["display_name"] or ""

        # Parse WP roles
        capabilities_raw = wp.get("capabilities_raw") or ""
        roles = parse_wp_capabilities(capabilities_raw)

        # Determine Learnami role from WP roles
        is_trusted = any(r in TRUSTED_ROLES for r in roles)
        is_admin = "administrator" in roles

        # Run our bot/spam evaluation
        eval_res = evaluate_registration(username, email)
        risk_score = eval_res["risk_score"]

        # Override: if WP says trusted/admin and risk is not extreme, grant trusted
        if is_trusted and risk_score < 0.85:
            assigned_role = "subscriber_trusted"
            can_post = True
            can_comment = True
            can_vote = True
            evaluation_status = "approved"
        elif risk_score >= 0.85:
            # Extreme risk — block even if WP says trusted (bots gained roles)
            assigned_role = "restricted_blocked"
            can_post = False
            can_comment = False
            can_vote = False
            evaluation_status = "rejected"
            blocked += 1
        elif risk_score >= 0.30:
            assigned_role = "subscriber_probationary"
            can_post = False
            can_comment = True
            can_vote = False
            evaluation_status = "flagged"
        else:
            assigned_role = eval_res["assigned_role"]
            can_post = False
            can_comment = True
            can_vote = False
            evaluation_status = eval_res["evaluation_status"]

        if assigned_role == "subscriber_trusted":
            trusted += 1

        # Bio from display_name as stub (real bio comes from usermeta)
        bio_stub = display_name if display_name and display_name != username else ""

        # Use WP registration date to set email_verified heuristic:
        # If user has been registered >30 days and has a trusted role → verified
        email_verified = is_trusted or (risk_score < 0.30)

        obj, is_created = UserOnboardingState.objects.update_or_create(
            wp_user_id=wp_id,
            defaults={
                "username": username,
                "email": email,
                "email_verified": email_verified,
                "bio": bio_stub,
                "evaluation_status": evaluation_status,
                "risk_score": risk_score,
                "risk_reasons": eval_res["risk_reasons"],
                "assigned_role": assigned_role,
                "onboarding_stage": "completed" if assigned_role == "subscriber_trusted" else eval_res["onboarding_stage"],
                "can_post": can_post,
                "can_comment": can_comment,
                "can_vote": can_vote,
            }
        )

        if is_created:
            created += 1
        else:
            updated += 1

    return {
        "wp_users_read": len(wp_users),
        "created": created,
        "updated": updated,
        "trusted": trusted,
        "blocked": blocked,
    }


def sync_wp_content_to_moderation(limit=200):
    """
    Sync WP posts and comments into ContentSubmission for moderation.
    Maps WP post_status to Learnami submission status:
      - 'publish' → 'approved' (already live on site)
      - 'pending' → 'submitted' (needs moderation)
      - 'draft' → 'submitted' (needs moderation)
    New comments are always 'submitted' for evaluation.
    Returns summary dict.
    """
    synced_posts = 0
    synced_comments = 0
    pending_for_review = 0

    # Sync Posts
    posts = get_wp_posts_for_moderation(limit=limit // 2)
    for p in posts:
        wp_post_id = p["ID"]
        author_id = p["post_author"] or 0
        author = p["user_login"] or f"wp_user_{author_id}"
        title = (p["post_title"] or "")[:255]
        body = (p["post_content"] or "")[:5000]
        post_type = p["post_type"] or "post"
        wp_status = p["post_status"] or "draft"

        # Map status
        if wp_status == "publish":
            learnami_status = "approved"
        elif wp_status in ("pending", "draft"):
            learnami_status = "submitted"
            pending_for_review += 1
        else:
            learnami_status = "submitted"
            pending_for_review += 1

        # content_type mapping
        ctype_map = {"post": "review", "review": "review", "forum": "forum_topic", "topic": "forum_topic"}
        ctype = ctype_map.get(post_type, "review")

        # Use wp_post_id as unique key via title+author to avoid duplicates
        ref_key = f"wp_post_{wp_post_id}"
        existing = ContentSubmission.objects.filter(
            wp_user_id=author_id,
            title=title[:100]  # short title match
        ).first()

        if not existing:
            ContentSubmission.objects.create(
                wp_user_id=author_id,
                author_username=author,
                content_type=ctype,
                title=title,
                body=body,
                status=learnami_status,
            )
            synced_posts += 1

    # Sync Comments
    comments = get_wp_comments_for_moderation(limit=limit // 2)
    for cm in comments:
        cm_id = cm["comment_ID"]
        author_id = cm["user_id"] or 0
        author = cm["comment_author"] or f"guest_{cm_id}"
        body = (cm["comment_content"] or "")[:5000]
        post_title = cm["post_title"] or "Comment"
        approved = str(cm["comment_approved"])

        if approved == "1":
            learnami_status = "approved"
        elif approved == "0":
            learnami_status = "submitted"
            pending_for_review += 1
        else:
            learnami_status = "submitted"
            pending_for_review += 1

        title = f"Comment on: {post_title}"[:255]

        existing = ContentSubmission.objects.filter(
            wp_user_id=author_id,
            title=title
        ).first()

        if not existing and body.strip():
            ContentSubmission.objects.create(
                wp_user_id=author_id,
                author_username=author,
                content_type="comment",
                title=title,
                body=body,
                status=learnami_status,
            )
            synced_comments += 1

    return {
        "posts_synced": synced_posts,
        "comments_synced": synced_comments,
        "pending_for_review": pending_for_review,
    }


def run_wp_full_sync(user_limit=500, content_limit=200):
    """
    Full WordPress → Learnami sync across all data types.
    Call this from the onboarding batch or orchestrator.
    """
    user_result = sync_wp_users_to_onboarding(limit=user_limit)
    content_result = sync_wp_content_to_moderation(limit=content_limit)

    GovernanceAuditLog.objects.create(
        actor_type="system",
        actor_id="wp_sync_engine",
        event_type="wp_data_sync",
        action="sync_users_and_content",
        result="allow",
        details={
            "users": user_result,
            "content": content_result,
        }
    )

    return {
        "sync_status": "completed",
        "users": user_result,
        "content": content_result,
    }
