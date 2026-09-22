from django.core.management.base import BaseCommand
from django.utils import timezone
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
from learnami.identity_engine import score_identity_candidate
from learnami.media_assistant import register_media_candidate
from learnami.policy_orchestration_engine import seed_policy_registry_and_sfps
from learnami.privacy_engine import record_consent, evaluate_privacy_access
from learnami.runbook_engine import start_runbook_execution, complete_runbook_execution
from learnami.blueprint_engine import create_blueprint_snapshot


class Command(BaseCommand):
    help = "Seeds exhaustive, rich starter data across ALL 25 models in Learnami."

    def handle(self, *args, **options):
        self.stdout.write("Seeding exhaustive demo data across ALL models...")

        # 1. SFPs (Workbook 9, 10)
        sfps = [
            ("CliqueFlicks", "CliqueFlicks Creator Hub & Fan Community", {"type": "creator_community", "modules": ["creator_helpers", "forum_moderation"]}),
            ("AppFlicks", "AppFlicks Taste Librarian & Discovery Engine", {"type": "taste_discovery", "modules": ["taste_librarian", "dedup_filter"]}),
            ("LearnamiOnboarding", "Learnami Internal Employee & Agent Onboarding", {"type": "internal_system", "modules": ["job_onboarding", "governance"]}),
            ("VotersForTruth", "Voters For Truth Political Discussion Portal", {"type": "political_forum", "modules": ["us_residency_check", "strict_moderation"]}),
            ("Flick2Shop", "Flick2Shop E-Commerce & Media Merchandise Hub", {"type": "ecommerce", "modules": ["merch_recommendations", "rights_check"]}),
        ]
        for key, name, caps in sfps:
            SFPRegistry.objects.update_or_create(
                sfp_key=key,
                defaults={"sfp_name": name, "capabilities_json": caps, "status": "active"}
            )

        # 2. Policy Rules (Workbook 5)
        policies = [
            ("registration_us_only_voters", "registration", "VotersForTruth", "restrict_country", {"allowed_countries": ["US"]}, 1),
            ("moderation_spam_filter", "moderation", "global", "flag_keywords", {"keywords": ["free crypto", "buy followers", "online casino", "cheap wire"]}, 1),
            ("governance_role_promotion", "governance", "global", "promote_trusted", {"min_age": 18, "require_avatar": True, "require_email": True}, 2),
            ("privacy_data_masking", "privacy", "global", "mask_pii", {"mask_fields": ["email", "ip_address", "location"]}, 1),
            ("media_min_resolution_policy", "media", "global", "min_dimensions", {"min_width": 600, "min_height": 600}, 2),
        ]
        for pkey, ptype, pctx, act, cfg, prio in policies:
            PolicyRule.objects.update_or_create(
                policy_key=pkey,
                defaults={
                    "policy_type": ptype,
                    "platform_context": pctx,
                    "action_type": act,
                    "rule_config": cfg,
                    "priority": prio,
                    "enabled": True,
                    "version": "v1.2"
                }
            )

        # 3. Users (Workbook 1 & 2)
        users_data = [
            (101, "alex_critic", "alex.critic@example.com", True, 28, "US", "Film buff and indie game reviewer.", True, "subscriber_trusted", "completed", True, True, True),
            (102, "spambot99_casino", "bot@mailinator.com", False, None, "RU", "", False, "restricted_blocked", "escalated", False, False, False),
            (103, "emma_writer", "emma.writer@gmail.com", True, 24, "CA", "Writer and book enthusiast.", True, "subscriber_probationary", "progressive_asks", True, True, False),
            (104, "sam_gamer", "sam.gamer@gmail.com", False, 19, "US", "Gamer looking for RPG lore.", False, "subscriber_probationary", "email_pending", False, True, False),
            (105, "maria_designer", "maria.designer@example.com", True, 31, "ES", "UI/UX designer and cinema reviewer.", True, "subscriber_trusted", "completed", True, True, True),
            (106, "david_curator", "david.curator@example.co.uk", True, 29, "UK", "Music curator and vinyl collector.", True, "subscriber_trusted", "completed", True, True, True),
            (107, "cyberbot404", "spam404@dispostable.com", False, 17, "CN", "Automated marketing bot", False, "restricted_blocked", "escalated", False, False, False),
            (108, "elena_filmmaker", "elena.film@example.org", True, 34, "US", "Independent director and essayist.", True, "subscriber_trusted", "completed", True, True, True),
            (109, "marcus_podcaster", "marcus.talks@example.net", True, 26, "US", "Audio producer & media critic.", True, "subscriber_trusted", "completed", True, True, True),
            (110, "suspicious_user_88", "anon88@tempmail.com", False, 15, "DE", "New profile", False, "subscriber_probationary", "progressive_asks", False, False, False),
        ]
        for wpid, uname, email, ev, age, loc, bio, av, role, stage, cp, cc, cv in users_data:
            eval_res = evaluate_registration(uname, email)
            UserOnboardingState.objects.update_or_create(
                wp_user_id=wpid,
                defaults={
                    "username": uname,
                    "email": email,
                    "email_verified": ev,
                    "age": age,
                    "location": loc,
                    "bio": bio,
                    "avatar_completed": av,
                    "evaluation_status": eval_res["evaluation_status"],
                    "risk_score": eval_res["risk_score"],
                    "risk_reasons": eval_res["risk_reasons"],
                    "onboarding_stage": stage,
                    "assigned_role": role,
                    "can_post": cp,
                    "can_comment": cc,
                    "can_vote": cv
                }
            )

        # 4. Submissions & Moderation Cases (Workbook 3)
        subs_data = [
            (101, "alex_critic", "review", "Dune: Part Two - Epic Sci-Fi Benchmark", "Denis Villeneuve delivers a breathtaking cinematic spectacle with unmatched sound design.", "approved"),
            (102, "spambot99_casino", "comment", "Get Free Crypto Now!", "Visit our online casino and get 100 free crypto spins instantly!", "flagged"),
            (104, "sam_gamer", "forum_topic", "Best RPGs of 2024", "Looking for recommendations on open world games with great lore.", "submitted"),
            (105, "maria_designer", "review", "Oppenheimer: Visual & Sound Triumph", "Christopher Nolan crafts an intense psychological masterpiece driven by Cillian Murphy's performance.", "approved"),
            (106, "david_curator", "review", "Hades II - Roguelike Perfection", "Supergiant Games refines their fluid combat loop and mythological storytelling in this sequel.", "approved"),
            (107, "cyberbot404", "comment", "Buy Cheap Followers Fast", "Boost your social media presence with 10k real cheap followers guaranteed!", "flagged"),
            (108, "elena_filmmaker", "review", "Past Lives: Subtlety in Cinema", "Celine Song crafts an aching, romantic debut about fate, memory, and unspoken connections.", "approved"),
            (109, "marcus_podcaster", "forum_topic", "Future of Spatial Audio in Cinema", "How Dolby Atmos and binaural audio are transforming theatrical soundscapes.", "approved"),
            (110, "suspicious_user_88", "comment", "Click Here For Free Wire Transfer", "Instant cash wire transfer available for all verified accounts click here now.", "flagged"),
        ]
        for wpid, author, ctype, title, body, status in subs_data:
            sub, created = ContentSubmission.objects.get_or_create(
                wp_user_id=wpid,
                title=title,
                defaults={
                    "author_username": author,
                    "content_type": ctype,
                    "body": body,
                    "status": status
                }
            )
            if status == "flagged":
                ModerationCase.objects.get_or_create(
                    submission=sub,
                    defaults={
                        "wp_user_id": wpid,
                        "reason_code": "SPAM",
                        "flagged_reason": "Detected restricted keyword match in body.",
                        "status": "open"
                    }
                )

        # 5. Governance Audit Logs (Workbook 4)
        audit_samples = [
            ("system", "wp_101", "registration_eval", "approve_registration", "allow", {"username": "alex_critic", "risk_score": 0.05}),
            ("system", "wp_102", "registration_eval", "flag_high_risk", "deny", {"username": "spambot99_casino", "risk_score": 0.95}),
            ("user_facing_admin_agent", "admin_01", "governance_check", "test_residency_rule", "allow", {"location": "US", "platform": "voters_for_truth"}),
            ("governance_admin_agent", "gov_02", "reaction_fired", "send_moderation_warning", "applied", {"target_user": 102}),
            ("system", "wp_105", "registration_eval", "auto_promote_trusted", "allow", {"username": "maria_designer"}),
            ("chief_of_staff", "cos_supervising", "release_readiness_audit", "passed", "allow", {"score": 100.0}),
        ]
        for actor_t, actor_i, ev_t, act, res, det in audit_samples:
            GovernanceAuditLog.objects.get_or_create(
                event_type=ev_t,
                action=act,
                actor_id=actor_i,
                defaults={"actor_type": actor_t, "result": res, "details": det}
            )

        # 6. Policy Change Requests & Release Readiness (Workbook 7)
        PolicyChangeRequest.objects.get_or_create(
            policy_key="moderation_spam_filter",
            requested_by="governance_admin_agent",
            defaults={
                "proposed_config": {"keywords": ["free crypto", "buy followers", "online casino", "phishing"]},
                "justification": "Add phishing protection to global spam filter.",
                "status": "approved",
                "reviewed_by": "chief_of_staff",
                "review_notes": "Approved for system rollout."
            }
        )

        ReleaseReadinessCheck.objects.get_or_create(
            scope_key="v12_consolidated_release",
            defaults={
                "scope_type": "core",
                "requested_by": "chief_of_staff",
                "status": "passed",
                "score": 98.5,
                "checks_json": {"policies": "passed", "governance": "passed", "privacy": "passed", "tests": "100% pass"}
            }
        )

        # 7. Orchestration Rules, Events, Simulations, Conflicts (Workbook 8, 9)
        rules = [
            ("rule_onboarding_to_moderation", "user_promoted", "onboarding", "moderation", "user_facing_admin_agent", {"can_post": True}, 1),
            ("rule_spam_flagged_to_governance", "content_flagged", "moderation", "governance", "governance_admin_agent", {"reason_code": "SPAM"}, 1),
            ("rule_identity_confirmed_to_memory", "link_confirmed", "identity", "memory", "chief_of_staff", {"confidence_min": 0.85}, 2),
        ]
        for rkey, ev, src, tgt, act, cond, prio in rules:
            OrchestrationRule.objects.update_or_create(
                rule_key=rkey,
                defaults={
                    "event_type": ev,
                    "source_layer": src,
                    "target_layer": tgt,
                    "target_actor": act,
                    "conditions": cond,
                    "priority": prio,
                    "enabled": True
                }
            )

        OrchestrationEventLog.objects.get_or_create(
            event_type="user_promoted",
            defaults={"source_actor": "onboarding_engine", "target_layer": "moderation", "payload": {"wp_user_id": 101}, "status": "dispatched"}
        )

        PolicySimulationResult.objects.get_or_create(
            simulation_name="master_policy_sim_v12",
            defaults={
                "policy_key": "moderation_spam_filter",
                "requested_by": "governance_admin_agent",
                "proposed_config": {"keywords": ["crypto", "casino"]},
                "sample_context": {"title": "Dune Review"},
                "result_summary": {"passed": True, "evaluated_count": 1},
                "passed": True
            }
        )

        SystemConflict.objects.get_or_create(
            conflict_type="policy_overlap",
            defaults={
                "severity": "low",
                "description": "Minor priority conflict between global spam policy and SFP-specific forum filter.",
                "status": "resolved",
                "reviewed_by": "chief_of_staff",
                "review_notes": "SFP specific rule configured with higher priority."
            }
        )

        ReplayLog.objects.get_or_create(
            replay_name="replay_moderation_event_batch",
            defaults={"event_type": "content_submission", "source_layer": "moderation", "payload": {"count": 6}, "status": "completed"}
        )

        ReviewCycle.objects.get_or_create(
            cycle_type="governance_periodic_review",
            defaults={"requested_by": "chief_of_staff", "status": "completed", "findings_json": {"compliant": True, "score": 100}}
        )

        # 8. Identity Candidate Links (Workbook 11)
        identities = [
            ("local_u_101", "sfp_gaming_hub", "global_user_9921", True, True, False, True),
            ("local_u_102", "sfp_film_forum", "global_user_8832", True, False, False, False),
            ("local_u_103", "sfp_music_review", "global_user_4419", False, True, True, True),
            ("local_u_105", "sfp_design_lab", "global_user_5520", True, True, True, True),
            ("local_u_108", "sfp_film_makers", "global_user_7712", True, True, True, True),
        ]
        for l_key, sfp, g_key, em, nm, pm, so in identities:
            scored = score_identity_candidate(em, nm, pm, so)
            IdentityCandidateLink.objects.update_or_create(
                local_user_key=l_key,
                candidate_global_user_key=g_key,
                defaults={
                    "sfp_name": sfp,
                    "confidence_score": scored["confidence_score"],
                    "link_reason": ",".join(scored["reasons"]),
                    "status": scored["status"]
                }
            )

        # 9. Retrieval Documents (Workbook 11)
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
            ("handbook_privacy_boundaries", "handbook", "sfp_privacy", "Privacy Access & Scope Boundaries",
             "Role-based matrix restricts cross-site user memory to verified governance admin agents and Chief of Staff supervisory layers.",
             {"security_level": "high"}),
        ]
        for k, dtype, sfp, title, content, meta in docs:
            RetrievalDocument.objects.update_or_create(
                doc_key=k,
                defaults={
                    "doc_type": dtype,
                    "sfp_name": sfp,
                    "title": title,
                    "content": content,
                    "metadata_json": meta,
                    "vector_status": "embedded"
                }
            )

        # 10. Module Analytics Snapshots (Workbook 11)
        ModuleAnalyticsSnapshot.objects.update_or_create(
            module_key="content_moderation",
            sfp_name="sfp_film_forum",
            defaults={"usage_count": 42, "approval_count": 35, "rejection_count": 5, "escalation_count": 2, "notes": {"efficiency": "94%"}}
        )

        ModuleAnalyticsSnapshot.objects.update_or_create(
            module_key="identity_resolution",
            sfp_name="sfp_core",
            defaults={"usage_count": 18, "approval_count": 15, "rejection_count": 2, "escalation_count": 1, "notes": {"accuracy": "92%"}}
        )

        # 11. Media Candidates & Review Drafts (Workbook 13)
        media_samples = [
            ("The Batman", "film", "The Batman Theatrical Poster", "https://image.tmdb.org/t/p/original/74xTEgt7R36Fpooo50r9T25onhq.jpg", 1000, 1500),
            ("Elden Ring", "game", "Elden Ring Key Art", "https://images.igdb.com/igdb/image/upload/t_cover_big/co4jni.jpg", 600, 800),
            ("Dune Part Two", "film", "Dune Part Two Teaser Poster", "https://image.tmdb.org/t/p/original/d5NGo2F75jUtLioGaMK5zVvODR.jpg", 1000, 1500),
            ("Oppenheimer", "film", "Oppenheimer IMAX Poster", "https://image.tmdb.org/t/p/original/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg", 1000, 1500),
            ("Random Album", "album", "Studio Album Cover", "https://i.discogs.com/album_art_square.jpg", 800, 800),
        ]
        for target, ctype, title, url, w, h in media_samples:
            register_media_candidate(target, ctype, title, url, w, h)

        batman_cand = MediaCandidate.objects.filter(post_target_title="The Batman").first()
        ReviewPostDraft.objects.update_or_create(
            title="The Batman: Neo-Noir Masterpiece",
            defaults={
                "content_type": "film",
                "mode": "assisted",
                "content_body": "Matt Reeves delivers a gritty, grounded detective thriller that redefines Gotham City.",
                "selected_media": batman_cand,
                "status": "packaged"
            }
        )

        dune_cand = MediaCandidate.objects.filter(post_target_title="Dune Part Two").first()
        ReviewPostDraft.objects.update_or_create(
            title="Dune: Part Two - Sci-Fi Milestone",
            defaults={
                "content_type": "film",
                "mode": "autonomous",
                "content_body": "Denis Villeneuve achieves legendary scale in this epic sci-fi conclusion.",
                "selected_media": dune_cand,
                "status": "synced"
            }
        )

        # 12. Privacy Access Logs & Consent Records (Workbook 12)
        evaluate_privacy_access("governance_admin_agent", "cross_site_memory", "global_user_9921")
        evaluate_privacy_access("user_facing_admin_agent", "moderation_history", "global_user_8832")
        evaluate_privacy_access("chief_of_staff", "identity_links", "global_user_5520")
        evaluate_privacy_access("guest", "user_pii", "global_user_1102")

        record_consent("global_user_9921", "cross_site_memory", True, "AppFlicks", {"method": "terms_agreement"})
        record_consent("global_user_8832", "cross_site_memory", False, "CliqueFlicks", {"method": "opt_out"})
        record_consent("global_user_5520", "cross_site_memory", True, "LearnamiOnboarding", {"method": "dashboard_opt_in"})
        record_consent("global_user_7712", "cross_site_memory", True, "Flick2Shop", {"method": "checkout_opt_in"})

        # 13. Runbook Executions, Blueprint Snapshots, Automation Logs (Workbook 12)
        rb1 = start_runbook_execution("policy_error_detected", "governance_admin_agent", "System policy verification test")
        complete_runbook_execution(rb1["execution_id"], "Verified self-healing policy quarantine.")

        rb2 = start_runbook_execution("moderation_surge", "user_facing_admin_agent", "Queue load balancing runbook")
        complete_runbook_execution(rb2["execution_id"], "Queue cleared successfully.")

        rb3 = start_runbook_execution("outage_recovery", "chief_of_staff", "Disaster recovery health check")
        complete_runbook_execution(rb3["execution_id"], "Failover recovery completed cleanly.")

        create_blueprint_snapshot("v12_consolidated_master_snapshot")

        AutomationTaskLog.objects.create(
            pipeline_name="Master Pipeline Execution",
            status="success",
            summary="All 25 models populated with rich starter data.",
            items_processed=100,
            details="Seeded complete dataset across all 13 Workbooks."
        )

        self.stdout.write(self.style.SUCCESS("EXHAUSTIVE SEED COMPLETE: All 25 models populated with rich starter data across all pages!"))
