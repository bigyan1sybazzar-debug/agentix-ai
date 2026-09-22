from django.urls import path
from . import views

urlpatterns = [
    # Web UI Dashboards (v1 - v13)
    path("", views.dashboard_view, name="dashboard"),
    path("db-settings/", views.db_settings_view, name="db_settings"),
    path("onboarding/", views.onboarding_view, name="onboarding"),
    path("moderation/", views.moderation_view, name="moderation"),
    path("governance/", views.governance_view, name="governance"),
    path("policies/", views.policy_registry_view, name="policy_registry"),
    path("identity/", views.identity_workbench_view, name="identity_workbench"),
    path("retrieval/", views.retrieval_workbench_view, name="retrieval_workbench"),
    path("privacy/", views.privacy_view, name="privacy"),
    path("runbooks/", views.runbooks_view, name="runbooks"),
    path("blueprint/", views.blueprint_view, name="blueprint"),
    path("media/", views.media_assistant_view, name="media_assistant"),
    path("analytics/", views.analytics_view, name="analytics"),
    path("run-automation/", views.trigger_self_automation, name="run_automation"),

    # REST APIs
    path("api/db/test/", views.api_test_mysql, name="api_test_mysql"),
    path("api/automation/run/", views.api_run_automation, name="api_run_automation"),
    path("api/identity/candidates/", views.api_identity_candidates, name="api_identity_candidates"),
    path("api/retrieval/documents/", views.api_retrieval_documents, name="api_retrieval_documents"),
    path("api/retrieval/documents/<int:doc_id>/embed/", views.api_retrieval_embed, name="api_retrieval_embed"),
    path("api/retrieval/query/", views.api_retrieval_query, name="api_retrieval_query"),
    path("api/media/evaluate/", views.api_media_evaluate, name="api_media_evaluate"),
]
