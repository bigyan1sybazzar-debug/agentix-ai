from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse

from .models import UserOnboardingState, ContentSubmission
from .registration_rules import evaluate_registration, evaluate_role_progression, run_automated_onboarding_batch


def _dashboard_modules():
    return {
        "registration": reverse("registration"),
        "admin": "/admin/",
    }


def dashboard_view(request):
    """Main dashboard — entry point into the system."""
    modules = _dashboard_modules()
    if request.method == "POST" and request.POST.get("action") == "enter":
        target = request.POST.get("target", "")
        url = modules.get(target)
        if url:
            return redirect(url)
        messages.error(request, f"Unknown section '{target}'.")
        return redirect("dashboard")

    users = UserOnboardingState.objects.all()
    context = {
        "modules": modules,
        "total_users": users.count(),
        "trusted_users": users.filter(assigned_role__icontains="trusted").count(),
        "probationary": users.filter(assigned_role__icontains="probationary").count(),
        "total_submissions": ContentSubmission.objects.count(),
    }
    return render(request, "learnami/dashboard.html", context)


def registration_view(request):
    """Registration risk evaluation & progressive profiling."""
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
            return redirect("registration")

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
            return redirect("registration")

        elif action == "run_onboarding_batch":
            res = run_automated_onboarding_batch()
            messages.success(request, f"Batch complete: {res['evaluated_count']} evaluated, {res['promoted_count']} auto-promoted to trusted!")
            return redirect("registration")

    users = UserOnboardingState.objects.all()
    context = {
        "users": users,
        "total_users": users.count(),
        "trusted_users": users.filter(assigned_role__icontains="trusted").count(),
        "probationary": users.filter(assigned_role__icontains="probationary").count(),
    }
    return render(request, "learnami/registration.html", context)
