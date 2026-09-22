from django.core.management.base import BaseCommand
from django.db import connection
from learnami.models import (
    UserOnboardingState, ContentSubmission, ModerationCase, GovernanceAuditLog,
    IdentityCandidateLink, RetrievalDocument, ModuleAnalyticsSnapshot,
    MediaCandidate, MediaProvenanceLog, ReviewPostDraft, AutomationTaskLog,
    PolicyRule, PolicyChangeRequest, ReleaseReadinessCheck, OrchestrationRule,
    OrchestrationEventLog, PolicySimulationResult, SystemConflict, ReplayLog,
    ReviewCycle, SFPRegistry, PrivacyAccessLog, ConsentRecord, RunbookExecution,
    SystemBlueprintSnapshot
)
from learnami.registration_rules import evaluate_registration


class Command(BaseCommand):
    help = "Flushes old mock data and imports real WordPress users, posts, and comments from 8uI_ tables."

    def handle(self, *args, **options):
        self.stdout.write("Flushing old mock data...")

        # Flush all Learnami tables
        ContentSubmission.objects.all().delete()
        UserOnboardingState.objects.all().delete()
        ModerationCase.objects.all().delete()
        GovernanceAuditLog.objects.all().delete()
        IdentityCandidateLink.objects.all().delete()
        RetrievalDocument.objects.all().delete()
        MediaCandidate.objects.all().delete()
        MediaProvenanceLog.objects.all().delete()
        ReviewPostDraft.objects.all().delete()
        PrivacyAccessLog.objects.all().delete()
        ConsentRecord.objects.all().delete()
        RunbookExecution.objects.all().delete()
        SystemBlueprintSnapshot.objects.all().delete()
        PolicyRule.objects.all().delete()
        SFPRegistry.objects.all().delete()
        OrchestrationRule.objects.all().delete()
        OrchestrationEventLog.objects.all().delete()
        PolicySimulationResult.objects.all().delete()
        SystemConflict.objects.all().delete()
        ReplayLog.objects.all().delete()
        ReviewCycle.objects.all().delete()
        PolicyChangeRequest.objects.all().delete()
        ReleaseReadinessCheck.objects.all().delete()

        self.stdout.write("Reading real WordPress site data (Read-Only on 8uI_ tables)...")

        with connection.cursor() as cur:
            # 1. Read real WP users safely
            cur.execute("SELECT ID, user_login, user_email, user_registered FROM 8uI_users ORDER BY ID ASC LIMIT 100;")
            wp_users = cur.fetchall()
            
            imported_users = 0
            for wpid, uname, email, reg_date in wp_users:
                eval_res = evaluate_registration(uname, email)
                UserOnboardingState.objects.create(
                    wp_user_id=wpid,
                    username=uname,
                    email=email,
                    email_verified=True,
                    evaluation_status=eval_res["evaluation_status"],
                    risk_score=eval_res["risk_score"],
                    risk_reasons=eval_res["risk_reasons"],
                    onboarding_stage="completed" if eval_res["evaluation_status"] == "approved" else "escalated",
                    assigned_role=eval_res["assigned_role"],
                    can_post=(eval_res["evaluation_status"] == "approved"),
                    can_comment=True,
                    can_vote=True
                )
                imported_users += 1

            # 2. Read real WP posts safely
            cur.execute("SELECT ID, post_author, post_title, post_content, post_type, post_status FROM 8uI_posts WHERE post_type IN ('post', 'page', 'review') AND post_status='publish' ORDER BY ID DESC LIMIT 50;")
            wp_posts = cur.fetchall()

            imported_posts = 0
            for pid, author_id, title, content, ptype, pstatus in wp_posts:
                author_user = UserOnboardingState.objects.filter(wp_user_id=author_id).first()
                author_name = author_user.username if author_user else f"wp_author_{author_id}"
                
                ContentSubmission.objects.create(
                    wp_user_id=author_id,
                    author_username=author_name,
                    content_type="review" if ptype == "review" else "forum_topic",
                    title=title[:250] if title else f"WP Post #{pid}",
                    body=content[:1000] if content else title,
                    status="approved"
                )
                imported_posts += 1

            # 3. Read real WP comments safely
            cur.execute("SELECT comment_ID, user_id, comment_author, comment_content, comment_approved FROM 8uI_comments ORDER BY comment_ID DESC LIMIT 30;")
            wp_comments = cur.fetchall()

            imported_comments = 0
            for cid, uid, author, content, app in wp_comments:
                cstatus = "approved" if app in ("1", 1, "approved") else "submitted"
                ContentSubmission.objects.create(
                    wp_user_id=uid if uid else 0,
                    author_username=author if author else f"commenter_{cid}",
                    content_type="comment",
                    title=f"Comment on Site Post #{cid}",
                    body=content[:500] if content else "Site comment",
                    status=cstatus
                )
                imported_comments += 1

        self.stdout.write(self.style.SUCCESS(f"REAL SITE DATA IMPORTED: Cleaned mock data and imported {imported_users} real WP users, {imported_posts} real WP posts, and {imported_comments} real WP comments!"))
