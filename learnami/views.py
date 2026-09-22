import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db import connection

from .models import (
    UserOnboardingState, ContentSubmission, ModerationCase, GovernanceAuditLog,
    IdentityCandidateLink, RetrievalDocument, ModuleAnalyticsSnapshot,
    MediaCandidate, MediaProvenanceLog, ReviewPostDraft, AutomationTaskLog,
    PrivacyAccessLog, ConsentRecord, RunbookExecution, SystemBlueprintSnapshot,
    PolicyRule, OrchestrationRule, SFPRegistry
)
from .db_helper import get_db_config, save_db_config, test_mysql_connection, auto_migrate
from .identity_engine import score_identity_candidate, create_identity_candidate_record, run_automated_identity_batch
from .vector_retrieval import embed_retrieval_document, retrieve_matches, run_automated_vector_embedding_batch
from .analytics_engine import create_module_analytics_snapshot, run_automated_analytics_telemetry
from .media_assistant import register_media_candidate, package_review_post, run_automated_media_validation, evaluate_media_asset
from .registration_rules import evaluate_registration, evaluate_role_progression, run_automated_onboarding_batch
from .content_moderation_rules import evaluate_content_submission, run_automated_moderation_batch, MODERATION_REASON_CODES
from .governance_rules import evaluate_governance_context, validate_profile_readiness, evaluate_reactions
from .policy_orchestration_engine import run_policy_simulation, run_release_readiness_audit
from .privacy_engine import evaluate_privacy_access, record_consent, evaluate_cross_site_memory
from .runbook_engine import list_runbooks, start_runbook_execution, complete_runbook_execution
from .blueprint_engine import get_production_blueprint, create_blueprint_snapshot
from .orchestrator import run_full_self_automation, seed_sample_starter_data
from .wp_sync_engine import run_wp_full_sync, sync_wp_users_to_onboarding, sync_wp_content_to_moderation



def get_current_db_status():
    """Returns information on the active database connection."""
    cfg = get_db_config()
    engine_name = connection.vendor
    is_mysql = (engine_name == "mysql")
    db_name = connection.settings_dict.get("NAME", "db.sqlite3")
    host = connection.settings_dict.get("HOST", "local")

    try:
        with connection.cursor() as cursor:
            tables = connection.introspection.table_names(cursor)
            learnami_tables = [t for t in tables if t.startswith((
                "user_onboarding", "content_submission", "moderation_case", "governance_audit",
                "identity_", "retrieval_", "module_", "media_", "review_", "automation_"
            ))]
    except Exception:
        learnami_tables = []

    return {
        "engine": engine_name,
        "is_mysql": is_mysql,
        "db_name": db_name,
        "host": host or "localhost",
        "tables_count": len(learnami_tables),
        "tables": learnami_tables,
        "config": cfg
    }


def dashboard_view(request):
    """Main executive dashboard across all Version layers."""
    db_status = get_current_db_status()
    users_count = UserOnboardingState.objects.count()
    trusted_users = UserOnboardingState.objects.filter(assigned_role__icontains="trusted").count()
    subs_count = ContentSubmission.objects.count()
    pending_mod = ModerationCase.objects.filter(status="open").count()
    identities_count = IdentityCandidateLink.objects.count()
    confirmed_identities = IdentityCandidateLink.objects.filter(status="confirmed").count()
    documents_count = RetrievalDocument.objects.count()
    embedded_docs = RetrievalDocument.objects.filter(vector_status="embedded").count()
    media_count = MediaCandidate.objects.count()
    approved_media = MediaCandidate.objects.filter(validation_status="approved").count()
    packaged_drafts = ReviewPostDraft.objects.filter(status="packaged").count()
    recent_logs = AutomationTaskLog.objects.all()[:6]

    context = {
        "db_status": db_status,
        "users_count": users_count,
        "trusted_users": trusted_users,
        "subs_count": subs_count,
        "pending_mod": pending_mod,
        "identities_count": identities_count,
        "confirmed_identities": confirmed_identities,
        "documents_count": documents_count,
        "embedded_docs": embedded_docs,
        "media_count": media_count,
        "approved_media": approved_media,
        "packaged_drafts": packaged_drafts,
        "recent_logs": recent_logs,
    }
    return render(request, "learnami/dashboard.html", context)


def db_settings_view(request):
    """cPanel MySQL credentials setup and test diagnostics."""
    cfg = get_db_config()
    db_status = get_current_db_status()
    test_result = None

    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "test":
            host = request.POST.get("host", "").strip()
            port = request.POST.get("port", "3306").strip()
            name = request.POST.get("name", "").strip()
            user = request.POST.get("user", "").strip()
            password = request.POST.get("password", "").strip()
            
            ok, msg, server_info = test_mysql_connection(host, port, name, user, password)
            test_result = {
                "success": ok,
                "message": msg,
                "server_info": server_info,
                "tested_host": host,
                "tested_user": user,
                "tested_db": name
            }

        elif action == "save_mysql":
            host = request.POST.get("host", "").strip()
            port = request.POST.get("port", "3306").strip()
            name = request.POST.get("name", "").strip()
            user = request.POST.get("user", "").strip()
            password = request.POST.get("password", "").strip()

            new_cfg = {
                "ENGINE": "mysql",
                "HOST": host,
                "PORT": port or "3306",
                "NAME": name,
                "USER": user,
                "PASSWORD": password,
                "OPTIONS": {"charset": "utf8mb4"}
            }
            save_db_config(new_cfg)
            messages.success(request, f"MySQL credentials saved for '{name}'@{host}! Please restart or reload to switch active connection.")
            return redirect("db_settings")

        elif action == "switch_sqlite":
            save_db_config({"ENGINE": "sqlite3", "NAME": "db.sqlite3"})
            messages.info(request, "Switched back to local SQLite database.")
            return redirect("db_settings")

        elif action == "auto_migrate":
            ok, msg = auto_migrate()
            if ok:
                messages.success(request, msg)
            else:
                messages.error(request, msg)
            return redirect("db_settings")

    context = {
        "cfg": cfg,
        "db_status": db_status,
        "test_result": test_result,
    }
    return render(request, "learnami/db_settings.html", context)


def trigger_self_automation(request):
    """Executes the master self-automation runner across all layers."""
    if request.method in ["POST", "GET"]:
        res = run_full_self_automation()
        messages.success(request, f"Full pipeline automation complete! {res['total_items']} items processed across v1 through v13.")
        return redirect("dashboard")
    return redirect("dashboard")


# =====================================================================
# WORKBOOK 1 & 2: Onboarding & Progressive Profiling View
# =====================================================================

def onboarding_view(request):
    """Onboarding, Email Verification & Progressive Asks (Workbook 1 & 2)."""
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "register_user":
            wpid = int(request.POST.get("wp_user_id", 105))
            uname = request.POST.get("username", "").strip()
            email = request.POST.get("email", "").strip()
            
            eval_res = evaluate_registration(uname, email)
            user_state = UserOnboardingState.objects.create(
                wp_user_id=wpid,
                username=uname,
                email=email,
                evaluation_status=eval_res["evaluation_status"],
                risk_score=eval_res["risk_score"],
                risk_reasons=eval_res["risk_reasons"],
                onboarding_stage=eval_res["onboarding_stage"],
                assigned_role=eval_res["assigned_role"]
            )
            messages.success(request, f"Registered '{uname}': Status {user_state.evaluation_status.upper()}, Role '{user_state.assigned_role}'")
            return redirect("onboarding")

        elif action == "update_asks":
            uid = request.POST.get("user_id")
            user = get_object_or_404(UserOnboardingState, id=uid)
            user.email_verified = "email_verified" in request.POST
            age_val = request.POST.get("age")
            user.age = int(age_val) if age_val else None
            user.location = request.POST.get("location", "").strip()
            user.bio = request.POST.get("bio", "").strip()
            user.avatar_completed = "avatar_completed" in request.POST
            
            changes = evaluate_role_progression(user)
            messages.success(request, f"Updated profile for '{user.username}'. Changes: {', '.join(changes) if changes else 'saved'}. Role: {user.assigned_role}")
            return redirect("onboarding")

        elif action == "run_onboarding_batch":
            res = run_automated_onboarding_batch()
            messages.success(request, f"Batch complete: {res['evaluated_count']} evaluated, {res['promoted_count']} auto-promoted to trusted!")
            return redirect("onboarding")

        elif action == "sync_wp_users":
            res = sync_wp_users_to_onboarding(limit=500)
            messages.success(
                request,
                f"WP Sync complete: {res['wp_users_read']} users read from WordPress. "
                f"{res['trusted']} trusted, {res['blocked']} blocked. "
                f"({res['created']} new, {res['updated']} updated)"
            )
            return redirect("onboarding")

    users = UserOnboardingState.objects.all()
    context = {
        "users": users,
        "total_users": users.count(),
        "trusted_users": users.filter(assigned_role__icontains="trusted").count(),
        "probationary": users.filter(assigned_role__icontains="probationary").count(),
    }
    return render(request, "learnami/onboarding.html", context)


# =====================================================================
# WORKBOOK 3: Content Participation & Moderation View
# =====================================================================

def moderation_view(request):
    """Content Participation, Creation Assistance & Moderation (Workbook 3)."""
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "submit_content":
            wpid = int(request.POST.get("wp_user_id", 101))
            user = UserOnboardingState.objects.filter(wp_user_id=wpid).first()
            author = user.username if user else f"user_{wpid}"
            ctype = request.POST.get("content_type", "review")
            title = request.POST.get("title", "").strip()
            body = request.POST.get("body", "").strip()

            sub = ContentSubmission.objects.create(
                wp_user_id=wpid,
                author_username=author,
                content_type=ctype,
                title=title,
                body=body,
                status="submitted"
            )
            evaluate_content_submission(sub.id)
            messages.success(request, f"Submitted '{title}'. Moderation status: {sub.status.upper()}")
            return redirect("moderation")

        elif action == "run_moderation_batch":
            res = run_automated_moderation_batch()
            messages.success(request, f"Moderation complete: {res['processed_count']} processed ({res['approved_count']} approved, {res['flagged_count']} flagged).")
            return redirect("moderation")

        elif action == "sync_wp_content":
            res = sync_wp_content_to_moderation(limit=200)
            messages.success(
                request,
                f"WP Content Sync: {res['posts_synced']} new posts + {res['comments_synced']} new comments synced. "
                f"{res['pending_for_review']} items queued for moderation review."
            )
            return redirect("moderation")

        elif action == "resolve_case":
            # Template sends submission_id (not case_id) — resolve by submission
            sub_id = request.POST.get("submission_id") or request.POST.get("case_id")
            decision = request.POST.get("decision")  # approved or rejected
            sub = get_object_or_404(ContentSubmission, id=sub_id)

            # Update submission status
            sub.status = decision
            sub.save()

            # Find or create associated moderation case
            case = ModerationCase.objects.filter(submission=sub).first()
            if case:
                case.status = f"resolved_{decision}"
                case.resolved_by = "moderator_admin"
                case.save()
                case_label = f"Case #{case.id}"
            else:
                # Direct resolve without a formal case record
                case_label = f"Submission #{sub.id}"

            if decision == "rejected":
                evaluate_reactions("moderation_rejected", {"wp_user_id": sub.wp_user_id, "submission_id": sub.id})
                messages.warning(request, f"{case_label} rejected. Automated governance reactions fired.")
            else:
                messages.success(request, f"{case_label} resolved: Content approved.")
            return redirect("moderation")

    status_filter = request.GET.get("status", "all")
    submissions = ContentSubmission.objects.all()
    cases = ModerationCase.objects.all()

    if status_filter == "approved":
        filtered_submissions = submissions.filter(status="approved")
    elif status_filter == "submitted" or status_filter == "pending":
        filtered_submissions = submissions.filter(status="submitted")
    elif status_filter == "flagged":
        filtered_submissions = submissions.filter(status="flagged")
    elif status_filter == "rejected":
        filtered_submissions = submissions.filter(status="rejected")
    else:
        filtered_submissions = submissions

    context = {
        "submissions": filtered_submissions,
        "all_submissions_count": submissions.count(),
        "cases": cases,
        "open_cases": cases.filter(status="open").count(),
        "submitted_count": submissions.filter(status="submitted").count(),
        "approved_count": submissions.filter(status="approved").count(),
        "flagged_count": submissions.filter(status="flagged").count(),
        "rejected_count": submissions.filter(status="rejected").count(),
        "reason_codes": MODERATION_REASON_CODES,
        "active_filter": status_filter,
    }
    return render(request, "learnami/moderation.html", context)



# =====================================================================
# WORKBOOK 4: Governance & Policy Sandbox View
# =====================================================================

def governance_view(request):
    """Governance, Validation & Reaction Rules Engine (Workbook 4)."""
    check_result = None
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "check_governance":
            wpid = int(request.POST.get("wp_user_id", 101))
            act = request.POST.get("user_action", "publish_post")
            ctx = request.POST.get("platform_context", "general")
            check_result = evaluate_governance_context(wpid, act, ctx)
            check_result["wp_user_id"] = wpid
            check_result["action"] = act
            check_result["context"] = ctx

    logs = GovernanceAuditLog.objects.all()[:20]
    users = UserOnboardingState.objects.all()
    context = {
        "logs": logs,
        "users": users,
        "check_result": check_result,
    }
    return render(request, "learnami/governance.html", context)


# =====================================================================
# WORKBOOK 11 & 13 Views
# =====================================================================

def identity_workbench_view(request):
    """Identity Resolution module UI (Workbook 11)."""
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create_candidate":
            local_user = request.POST.get("local_user_key", "").strip()
            sfp = request.POST.get("sfp_name", "").strip()
            global_user = request.POST.get("candidate_global_user_key", "").strip()
            em = "email_match" in request.POST
            nm = "name_match" in request.POST
            pm = "phone_match" in request.POST
            so = "sfp_overlap" in request.POST
            
            cand = create_identity_candidate_record(local_user, sfp, global_user, em, nm, pm, so)
            messages.success(request, f"Created identity candidate for '{local_user}'. Score: {cand.confidence_score:.2f} ({cand.status})")
            return redirect("identity_workbench")

        elif action == "run_batch":
            res = run_automated_identity_batch()
            messages.success(request, f"Batch complete: {res['processed']} evaluated, {res['auto_confirmed']} auto-confirmed.")
            return redirect("identity_workbench")

        elif action == "update_status":
            cand_id = request.POST.get("candidate_id")
            new_status = request.POST.get("new_status")
            cand = get_object_or_404(IdentityCandidateLink, id=cand_id)
            cand.status = new_status
            cand.reviewed_by = "admin_user"
            cand.save()
            messages.info(request, f"Updated candidate {cand_id} to '{new_status}'.")
            return redirect("identity_workbench")

    candidates = IdentityCandidateLink.objects.all()
    context = {
        "candidates": candidates,
        "total_candidates": candidates.count(),
        "confirmed": candidates.filter(status="confirmed").count(),
        "pending": candidates.filter(status__in=["candidate", "review_candidate", "high_confidence_candidate"]).count(),
    }
    return render(request, "learnami/identity.html", context)


def retrieval_workbench_view(request):
    """Vector Memory & Semantic RAG Retrieval UI (Workbook 11)."""
    query_result = None
    search_query = ""

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_document":
            doc_key = request.POST.get("doc_key", "").strip()
            doc_type = request.POST.get("doc_type", "policy")
            sfp_name = request.POST.get("sfp_name", "").strip()
            title = request.POST.get("title", "").strip()
            content = request.POST.get("content", "").strip()
            auto_embed = "auto_embed" in request.POST

            doc = RetrievalDocument.objects.create(
                doc_key=doc_key,
                doc_type=doc_type,
                sfp_name=sfp_name,
                title=title,
                content=content,
                vector_status="pending"
            )
            if auto_embed:
                embed_retrieval_document(doc.id)
                messages.success(request, f"Document '{title or doc_key}' saved and embedded into vector memory.")
            else:
                messages.success(request, f"Document '{title or doc_key}' saved with status pending.")
            return redirect("retrieval_workbench")

        elif action == "embed_all":
            res = run_automated_vector_embedding_batch()
            messages.success(request, f"Embedded {res['embedded_count']} pending documents into vector space.")
            return redirect("retrieval_workbench")

        elif action == "search":
            search_query = request.POST.get("query", "").strip()
            if search_query:
                query_result = retrieve_matches(search_query, limit=5)

    docs = RetrievalDocument.objects.all()
    context = {
        "documents": docs,
        "total_docs": docs.count(),
        "embedded_docs": docs.filter(vector_status="embedded").count(),
        "query_result": query_result,
        "search_query": search_query,
    }
    return render(request, "learnami/retrieval.html", context)


def media_assistant_view(request):
    """Review Post Media Assistant module UI (Workbook 13)."""
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add_candidate":
            target = request.POST.get("post_target_title", "").strip()
            ctype = request.POST.get("content_type", "film")
            title = request.POST.get("title", "").strip()
            url = request.POST.get("source_url", "").strip()
            w = int(request.POST.get("width", 800) or 800)
            h = int(request.POST.get("height", 1200) or 1200)

            cand = register_media_candidate(target, ctype, title, url, w, h)
            messages.success(request, f"Discovered candidate: '{title}'. Quality Score: {cand.quality_score:.1f} ({cand.validation_status})")
            return redirect("media_assistant")

        elif action == "create_post":
            title = request.POST.get("post_title", "").strip()
            ctype = request.POST.get("content_type", "film")
            cand_id = request.POST.get("selected_media_id")
            body = request.POST.get("content_body", "").strip()
            mode = request.POST.get("mode", "assisted")

            selected_cand = MediaCandidate.objects.filter(id=cand_id).first() if cand_id else None
            draft = ReviewPostDraft.objects.create(
                title=title,
                content_type=ctype,
                mode=mode,
                content_body=body,
                selected_media=selected_cand,
                status="draft"
            )
            package_review_post(draft.id, mode=mode)
            messages.success(request, f"Packaged Review Post '{title}' with complete Learnami WordPress post-meta!")
            return redirect("media_assistant")

        elif action == "run_auto_validation":
            res = run_automated_media_validation()
            messages.success(request, f"Revalidated {res['revalidated_candidates']} candidates, auto-packaged {res['auto_packaged_drafts']} posts.")
            return redirect("media_assistant")

    candidates = MediaCandidate.objects.all()
    drafts = ReviewPostDraft.objects.all()
    logs = MediaProvenanceLog.objects.all()[:10]

    context = {
        "candidates": candidates,
        "drafts": drafts,
        "provenance_logs": logs,
        "total_candidates": candidates.count(),
        "approved_candidates": candidates.filter(validation_status="approved").count(),
    }
    return render(request, "learnami/media.html", context)


def analytics_view(request):
    """Module-level analytics & telemetry dashboard (Workbook 11)."""
    if request.method == "POST":
        res = run_automated_analytics_telemetry()
        messages.success(request, f"Generated {res['snapshots_count']} live telemetry snapshots.")
        return redirect("analytics")

    snapshots = ModuleAnalyticsSnapshot.objects.all()
    identity_snaps = snapshots.filter(module_key="identity_resolution")[:1]
    media_snaps = snapshots.filter(module_key="media_assistant")[:1]
    retrieval_snaps = snapshots.filter(module_key="retrieval_engine")[:1]

    context = {
        "snapshots": snapshots,
        "identity_stat": identity_snaps.first(),
        "media_stat": media_snaps.first(),
        "retrieval_stat": retrieval_snaps.first(),
    }
    return render(request, "learnami/analytics.html", context)


# ==========================================
# REST API Endpoints
# ==========================================

@csrf_exempt
def api_test_mysql(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            host = data.get("host", "")
            port = data.get("port", "3306")
            name = data.get("name", "")
            user = data.get("user", "")
            password = data.get("password", "")
            ok, msg, server_info = test_mysql_connection(host, port, name, user, password)
            return JsonResponse({"success": ok, "message": msg, "server_info": server_info})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)
    return JsonResponse({"error": "POST required"}, status=405)


@csrf_exempt
def api_run_automation(request):
    res = run_full_self_automation()
    return JsonResponse(res)


@csrf_exempt
def api_identity_candidates(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            cand = create_identity_candidate_record(
                local_user_key=data.get("local_user_key"),
                sfp_name=data.get("sfp_name"),
                candidate_global_user_key=data.get("candidate_global_user_key"),
                email_match=data.get("email_match", False),
                name_match=data.get("name_match", False),
                phone_match=data.get("phone_match", False),
                sfp_overlap=data.get("sfp_overlap", False)
            )
            return JsonResponse({
                "id": cand.id,
                "local_user_key": cand.local_user_key,
                "candidate_global_user_key": cand.candidate_global_user_key,
                "confidence_score": cand.confidence_score,
                "status": cand.status,
                "link_reason": cand.link_reason
            }, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    candidates = list(IdentityCandidateLink.objects.values(
        "id", "local_user_key", "sfp_name", "candidate_global_user_key",
        "confidence_score", "link_reason", "status", "created_at"
    ))
    return JsonResponse(candidates, safe=False)


@csrf_exempt
def api_retrieval_documents(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            doc = RetrievalDocument.objects.create(
                doc_key=data.get("doc_key"),
                doc_type=data.get("doc_type", "policy"),
                sfp_name=data.get("sfp_name"),
                title=data.get("title"),
                content=data.get("content", ""),
                metadata_json=data.get("metadata_json", {}),
                vector_status="pending"
            )
            return JsonResponse({
                "id": doc.id,
                "doc_key": doc.doc_key,
                "vector_status": doc.vector_status,
                "title": doc.title
            }, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    docs = list(RetrievalDocument.objects.values("id", "doc_key", "doc_type", "title", "vector_status"))
    return JsonResponse(docs, safe=False)


@csrf_exempt
def api_retrieval_embed(request, doc_id):
    doc = embed_retrieval_document(doc_id)
    if not doc:
        return JsonResponse({"error": "Document not found or embedding failed"}, status=404)
    return JsonResponse({
        "id": doc.id,
        "doc_key": doc.doc_key,
        "vector_status": doc.vector_status,
        "vector_dimensions": len(doc.embedding_json or [])
    })


@csrf_exempt
def api_retrieval_query(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            query = data.get("query", "")
            limit = int(data.get("limit", 5))
            res = retrieve_matches(query, limit)
            return JsonResponse(res)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "POST required"}, status=405)


@csrf_exempt
def api_media_evaluate(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            url = data.get("source_url", "")
            ctype = data.get("content_type", "film")
            w = int(data.get("width", 800))
            h = int(data.get("height", 1200))
            res = evaluate_media_asset(ctype, url, w, h)
            return JsonResponse(res)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "POST required"}, status=405)


def privacy_view(request):
    """Workbook 12: Privacy Boundaries & Consent Management UI."""
    access_logs = PrivacyAccessLog.objects.all()[:20]
    consent_records = ConsentRecord.objects.all()[:20]
    
    check_result = None
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "access_check":
            role = request.POST.get("requester_role", "user_facing_admin_agent")
            dclass = request.POST.get("data_class", "cross_site_memory")
            key = request.POST.get("target_key", "global_user_9921")
            check_result = evaluate_privacy_access(role, dclass, key)
            messages.success(request, f"Privacy check evaluated: {check_result['decision'].upper()}")
        elif action == "grant_consent":
            gkey = request.POST.get("global_user_key", "global_user_9921")
            ctype = request.POST.get("consent_type", "cross_site_memory")
            granted = (request.POST.get("granted") == "true")
            sfp = request.POST.get("source_sfp", "AppFlicks")
            record_consent(gkey, ctype, granted, sfp, {"method": "admin_ui_toggle"})
            messages.success(request, f"Consent for {gkey} recorded as {granted}.")

    return render(request, "learnami/privacy.html", {
        "access_logs": access_logs,
        "consent_records": consent_records,
        "check_result": check_result,
        "db_status": get_current_db_status()
    })


def runbooks_view(request):
    """Workbook 12: Operational Runbooks Execution UI."""
    catalog = list_runbooks()
    executions = RunbookExecution.objects.all()[:20]
    run_result = None

    if request.method == "POST":
        rkey = request.POST.get("runbook_key")
        by = request.POST.get("triggered_by", "admin_dashboard")
        run_result = start_runbook_execution(rkey, by, "Triggered via Admin UI")
        complete_runbook_execution(run_result["execution_id"], "Finished runbook steps via UI trigger.")
        messages.success(request, f"Runbook [{rkey}] executed successfully.")

    return render(request, "learnami/runbooks.html", {
        "catalog": catalog,
        "executions": executions,
        "run_result": run_result,
        "db_status": get_current_db_status()
    })


def blueprint_view(request):
    """Workbook 12: System Production Blueprint & Snapshot UI."""
    blueprint = get_production_blueprint()
    snapshots = SystemBlueprintSnapshot.objects.all()[:10]

    if request.method == "POST":
        sname = request.POST.get("snapshot_name", "manual_admin_snapshot")
        create_blueprint_snapshot(sname)
        messages.success(request, f"Blueprint snapshot '{sname}' created successfully.")

    return render(request, "learnami/blueprint.html", {
        "blueprint": blueprint,
        "snapshots": snapshots,
        "db_status": get_current_db_status()
    })


def policy_registry_view(request):
    """Workbooks 5-10: Policy Rules, SFPs & Simulation UI."""
    policies = PolicyRule.objects.all()
    sfps = SFPRegistry.objects.all()
    rules = OrchestrationRule.objects.all()
    sim_result = None

    if request.method == "POST":
        pkey = request.POST.get("policy_key", "moderation_spam_filter")
        sname = request.POST.get("simulation_name", "manual_sandbox_test")
        sim_result = run_policy_simulation(sname, pkey, {"sample": "test payload"})
        messages.success(request, f"Policy simulation '{sname}' finished (Passed: {sim_result['passed']}).")

    return render(request, "learnami/policy_registry.html", {
        "policies": policies,
        "sfps": sfps,
        "rules": rules,
        "sim_result": sim_result,
        "db_status": get_current_db_status()
    })


