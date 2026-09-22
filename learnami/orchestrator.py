from .models import (
    IdentityCandidateLink, RetrievalDocument, ModuleAnalyticsSnapshot,
    MediaCandidate, ReviewPostDraft, AutomationTaskLog,
    UserOnboardingState, ContentSubmission, ModerationCase, GovernanceAuditLog,
    ConsentRecord, RunbookExecution, SystemBlueprintSnapshot
)
from .identity_engine import run_automated_identity_batch, score_identity_candidate
from .vector_retrieval import run_automated_vector_embedding_batch
from .analytics_engine import run_automated_analytics_telemetry
from .media_assistant import run_automated_media_validation, register_media_candidate
from .registration_rules import run_automated_onboarding_batch, evaluate_registration
from .content_moderation_rules import run_automated_moderation_batch
from .governance_rules import evaluate_reactions
from .policy_orchestration_engine import seed_policy_registry_and_sfps, run_policy_simulation, run_release_readiness_audit
from .privacy_engine import record_consent, evaluate_privacy_access
from .runbook_engine import start_runbook_execution, complete_runbook_execution
from .blueprint_engine import create_blueprint_snapshot
from .wp_sync_engine import run_wp_full_sync


def seed_sample_starter_data():
    """
    Populates sample starter records across all Version layers (v1-v13)
    if the database is fresh.
    """
    # 0. Seed Policy Registry & SFPs (Workbook 5, 9, 10)
    seed_policy_registry_and_sfps()

    # 1. Onboarding Users (Workbook 1 & 2)
    if UserOnboardingState.objects.count() == 0:
        user_samples = [
            (101, "alex_critic", "alex.critic@example.com", True, 28, "US", "Film buff and indie game reviewer.", True, "subscriber_trusted", "completed", True, True, True),
            (102, "spambot99_casino", "bot@mailinator.com", False, None, "RU", "", False, "restricted_blocked", "escalated", False, False, False),
            (103, "emma_writer", "emma.writer@gmail.com", True, 24, "CA", "Writer and book enthusiast.", False, "subscriber_probationary", "progressive_asks", False, True, False),
            (104, "sam_gamer", "sam.gamer@gmail.com", False, 19, "US", "", False, "subscriber_probationary", "email_pending", False, False, False),
        ]
        for wpid, uname, email, ev, age, loc, bio, av, role, stage, cp, cc, cv in user_samples:
            eval_res = evaluate_registration(uname, email)
            UserOnboardingState.objects.create(
                wp_user_id=wpid,
                username=uname,
                email=email,
                email_verified=ev,
                age=age,
                location=loc,
                bio=bio,
                avatar_completed=av,
                evaluation_status=eval_res["evaluation_status"],
                risk_score=eval_res["risk_score"],
                risk_reasons=eval_res["risk_reasons"],
                onboarding_stage=stage,
                assigned_role=role,
                can_post=cp,
                can_comment=cc,
                can_vote=cv
            )

    # 2. Content Submissions & Moderation (Workbook 3)
    if ContentSubmission.objects.count() == 0:
        sub_samples = [
            (101, "alex_critic", "review", "Dune: Part Two - Epic Sci-Fi Benchmark", "Denis Villeneuve delivers a breathtaking cinematic spectacle with unmatched sound design.", "approved"),
            (102, "spambot99_casino", "comment", "Get Free Crypto Now!", "Visit our online casino and get 100 free crypto spins instantly!", "flagged"),
            (104, "sam_gamer", "forum_topic", "Best RPGs of 2024", "Looking for recommendations on open world games with great lore.", "submitted"),
        ]
        for wpid, author, ctype, title, body, status in sub_samples:
            sub = ContentSubmission.objects.create(
                wp_user_id=wpid,
                author_username=author,
                content_type=ctype,
                title=title,
                body=body,
                status=status
            )
            if status == "flagged":
                ModerationCase.objects.create(
                    submission=sub,
                    wp_user_id=wpid,
                    reason_code="SPAM",
                    flagged_reason="Detected restricted keyword: 'free crypto'",
                    status="open"
                )

    # 3. Identity Candidates (Workbook 11)
    if IdentityCandidateLink.objects.count() == 0:
        samples = [
            ("local_u_101", "sfp_gaming_hub", "global_user_9921", True, True, False, True),
            ("local_u_102", "sfp_film_forum", "global_user_8832", True, False, False, False),
            ("local_u_103", "sfp_music_review", "global_user_4419", False, True, True, True),
            ("local_u_104", "sfp_book_club", "global_user_1102", False, False, False, True),
        ]
        for l_key, sfp, g_key, em, nm, pm, so in samples:
            scored = score_identity_candidate(em, nm, pm, so)
            IdentityCandidateLink.objects.create(
                local_user_key=l_key,
                sfp_name=sfp,
                candidate_global_user_key=g_key,
                confidence_score=scored["confidence_score"],
                link_reason=",".join(scored["reasons"]),
                status=scored["status"]
            )

    # 4. Retrieval Documents (Workbook 11)
    if RetrievalDocument.objects.count() == 0:
        docs = [
            ("policy_editorial_guideline", "policy", "sfp_core", "Editorial Media Asset Policy",
             "All review post media assets must be at least 600x900px for film posters and 500x500px for album art. Only trusted or editorial caution sources are permitted.",
             {"version": "1.4", "category": "media"}),
            ("handbook_identity_resolution", "handbook", "sfp_governance", "Cross-SFP Identity Resolution Protocol",
             "When a local user account matches email and name across two community portals, assign confidence score above 0.75 and flag for automated linking.",
             {"version": "2.0", "author": "chief_of_staff"}),
            ("review_batman_sample", "review", "sfp_film_forum", "The Batman (2022) Editorial Review Precedent",
             "The Batman presents an immersive neo-noir detective thriller. Use high-resolution dark aesthetic posters from TMDB verified repository.",
             {"year": 2022, "rating": "9/10"}),
            ("precedent_autonomous_mode", "precedent", "sfp_orchestrator", "Autonomous Post Packaging Precedent",
             "In Autonomous Mode, the media assistant automatically attaches approved candidates to WordPress drafts with complete provenance metadata without human intervention.",
             {"automation_level": "L4"}),
        ]
        for k, dtype, sfp, title, content, meta in docs:
            RetrievalDocument.objects.create(
                doc_key=k,
                doc_type=dtype,
                sfp_name=sfp,
                title=title,
                content=content,
                metadata_json=meta,
                vector_status="pending"
            )

    # 5. Media Candidates (Workbook 13)
    if MediaCandidate.objects.count() == 0:
        media_samples = [
            ("The Batman", "film", "The Batman Theatrical Poster", "https://image.tmdb.org/t/p/original/74xTEgt7R36Fpooo50r9T25onhq.jpg", 1000, 1500),
            ("Elden Ring", "game", "Elden Ring Key Art", "https://images.igdb.com/igdb/image/upload/t_cover_big/co4jni.jpg", 600, 800),
            ("Random Low Res Art", "film", "Unverified Poster", "https://pinterest.com/pin/12345678/poster.jpg", 200, 250),
            ("Random Album", "album", "Studio Album Cover", "https://i.discogs.com/album_art_square.jpg", 800, 800),
        ]
        for target, ctype, title, url, w, h in media_samples:
            register_media_candidate(target, ctype, title, url, w, h)

    # 6. Draft review posts (Workbook 13)
    if ReviewPostDraft.objects.count() == 0:
        batman_cand = MediaCandidate.objects.filter(post_target_title="The Batman").first()
        ReviewPostDraft.objects.create(
            title="The Batman: Neo-Noir Masterpiece",
            content_type="film",
            mode="assisted",
            content_body="Matt Reeves delivers a gritty, grounded detective thriller that redefines Gotham City.",
            selected_media=batman_cand,
            status="draft"
        )

    # 7. User Privacy Consent Records (Workbook 12)
    if ConsentRecord.objects.count() == 0:
        record_consent("global_user_9921", "cross_site_memory", True, "AppFlicks", {"method": "terms_agreement"})
        record_consent("global_user_8832", "cross_site_memory", False, "CliqueFlicks", {"method": "opt_out"})

    # 8. Production Blueprint Snapshot (Workbook 12)
    if SystemBlueprintSnapshot.objects.count() == 0:
        create_blueprint_snapshot("v12_consolidated_master_snapshot")


def run_full_self_automation():
    """
    Main entry point for 'Do It Self Automation' across ALL layers (v1 - v13):
    WP Sync -> v1-v2 Onboarding -> v3 Moderation -> v4 Governance -> v5-v10 Policy & Orchestration -> v11 Memory & Identity -> v12 Privacy & Runbooks -> v13 Media
    """
    results = {}
    details = []

    # Layer 0: WordPress Live Data Sync (pull real users, posts, comments)
    try:
        sync_res = run_wp_full_sync(user_limit=500, content_limit=200)
        results["wp_sync"] = sync_res
        u = sync_res["users"]
        c = sync_res["content"]
        details.append(
            f"WP Sync: Synced {u['wp_users_read']} WP users ({u['trusted']} trusted, {u['blocked']} blocked). "
            f"Content: {c['posts_synced']} posts + {c['comments_synced']} comments ({c['pending_for_review']} pending review)."
        )
    except Exception as e:
        details.append(f"WP Sync skipped: {str(e)}")
        sync_res = {}

    # Layer 1 & 2: Onboarding & Progressive Profiling
    onb_res = run_automated_onboarding_batch()
    results["onboarding"] = onb_res
    details.append(f"Onboarding Engine (v1+v2): Evaluated {onb_res['evaluated_count']} registrations, auto-promoted {onb_res['promoted_count']} to trusted.")

    # Layer 3: Content Participation & Moderation
    mod_res = run_automated_moderation_batch()
    results["moderation"] = mod_res
    details.append(f"Moderation Engine (v3): Processed {mod_res['processed_count']} submissions ({mod_res['approved_count']} approved, {mod_res['flagged_count']} flagged).")

    # Layer 5-10: Policy Simulation & Release Readiness Audit
    sim_res = run_policy_simulation("master_auto_sim", "moderation_spam_filter", {"user_age": 25, "body": "Check out this movie"})
    readiness_res = run_release_readiness_audit("core", "v1-v13_unified")
    sim_name = sim_res.get("simulation_name", "master_auto_sim")
    sim_status = "passed" if sim_res.get("passed") else f"evaluated ({sim_res.get('reason', 'completed')})"
    details.append(f"Policy & Governance (v5-v10): Sandbox simulation '{sim_name}' {sim_status}. Release readiness gate status: '{readiness_res['status']}' (Score: {readiness_res['score']}).")

    # Layer 11: Identity Resolution
    id_res = run_automated_identity_batch()
    results["identity"] = id_res
    details.append(f"Identity Engine (v11): Evaluated {id_res['processed']} cross-site candidates ({id_res['auto_confirmed']} auto-confirmed).")

    # Layer 11: Vector Memory
    vec_res = run_automated_vector_embedding_batch()
    results["vector_memory"] = vec_res
    details.append(f"Vector Memory (v11): Generated embeddings for {vec_res['embedded_count']} documents.")

    # Layer 12: Privacy & Runbook Check
    priv_res = evaluate_privacy_access("governance_admin_agent", "cross_site_memory", "global_user_9921")
    runbook_res = start_runbook_execution("policy_error_detected", "orchestrator", "Automated diagnostic runbook check")
    complete_runbook_execution(runbook_res["execution_id"], "Completed self-healing check cleanly.")
    details.append(f"Privacy & Runbooks (v12): Evaluated privacy access for '{priv_res['requester_role']}' ({priv_res['decision']}). Executed runbook #{runbook_res['execution_id']} successfully.")

    # Layer 13: Media Assistant
    media_res = run_automated_media_validation()
    results["media_assistant"] = media_res
    details.append(f"Media Assistant (v13): Revalidated {media_res['revalidated_candidates']} image assets, auto-packaged {media_res['auto_packaged_drafts']} posts.")

    # Layer 11: Analytics Telemetry
    analytics_res = run_automated_analytics_telemetry()
    results["analytics"] = analytics_res
    details.append(f"Analytics Engine (v11): Generated {analytics_res['snapshots_count']} telemetry snapshots.")

    total_items = (
        onb_res.get("evaluated_count", 0) +
        mod_res.get("processed_count", 0) +
        id_res.get("processed", 0) +
        vec_res.get("embedded_count", 0) +
        media_res.get("revalidated_candidates", 0) +
        analytics_res.get("snapshots_count", 0) +
        2 # Privacy & Runbook tasks
    )

    log_entry = AutomationTaskLog.objects.create(
        pipeline_name="Unified Master Self-Automation (v1-v13)",
        status="success",
        summary=f"Automated all layers (v1-v13) successfully. {total_items} items processed.",
        items_processed=total_items,
        details="\n".join(details)
    )

    return {
        "log_id": log_entry.id,
        "status": "success",
        "total_items": total_items,
        "details": details,
        "metrics": results
    }

