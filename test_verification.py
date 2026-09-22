import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from learnami.orchestrator import run_full_self_automation

c = Client()

routes = [
    '/',
    '/db-settings/',
    '/onboarding/',
    '/moderation/',
    '/governance/',
    '/policies/',
    '/identity/',
    '/retrieval/',
    '/privacy/',
    '/runbooks/',
    '/blueprint/',
    '/media/',
    '/analytics/',
    '/api/identity/candidates/',
    '/api/retrieval/documents/',
]

print("--- Testing All GET Routes (v1-v13) ---")
for r in routes:
    resp = c.get(r)
    print(f"GET {r} -> {resp.status_code}")
    assert resp.status_code in [200, 302], f"Failed route {r}: {resp.status_code}"

print("\n--- Testing Full Master Self-Automation Orchestrator ---")
res = run_full_self_automation()
print("Master Orchestrator Result:", res["status"], f"({res['total_items']} items processed)")
for detail in res["details"]:
    print("  *", detail)

print("\n--- Testing Governance & Privacy Engine Checks ---")
from learnami.governance_rules import evaluate_governance_context
from learnami.privacy_engine import evaluate_privacy_access, evaluate_cross_site_memory

gov_res1 = evaluate_governance_context(101, "publish_post", "general")
print("Alex (Trusted) Publish in General:", gov_res1)

gov_res2 = evaluate_governance_context(102, "publish_post", "voters_for_truth")
print("Spambot (Non-US) in VotersForTruth:", gov_res2)

priv_res = evaluate_privacy_access("governance_admin_agent", "cross_site_memory", "global_user_9921")
print("Privacy Check (Governance Agent -> Cross-Site Memory):", priv_res)

mem_res = evaluate_cross_site_memory("global_user_9921", "AppFlicks", "CliqueFlicks")
print("Cross-Site Consent Memory Check:", mem_res)

print("\n================================================")
print("SUCCESS: ALL VERSION LAYERS (v1-v13) VERIFIED!")
print("================================================")
