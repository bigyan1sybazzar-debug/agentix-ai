from django.core.management.base import BaseCommand
from learnami.models import UserOnboardingState
from learnami.registration_rules import evaluate_registration

WP_USERS = [
    {"username": "0thz91", "wp_user_id": 7040, "email": "easyasswinsman@thinhmin.com", "wp_role": "Subscriber"},
    {"username": "1hfjkf23", "wp_user_id": 8366, "email": "9482@gmail.com", "wp_role": "AppFlicker Critic"},
    {"username": "1snfvs", "wp_user_id": 7366, "email": "romnik2012@code-gmail.com", "wp_role": "Subscriber"},
    {"username": "1xbet_ctei", "wp_user_id": 8624, "email": "rfydrsqwwei@1win-aviator-casino.store", "wp_role": "AppFlicker Critic"},
    {"username": "20", "wp_user_id": 8617, "email": "tuopoty@gmail.com", "wp_role": "AppFlicker Critic"},
    {"username": "3aplus63.ru", "wp_user_id": 7225, "email": "fgrggfg@gmail.ru", "wp_role": "AppFlicker Critic"},
    {"username": "40pa7o", "wp_user_id": 7039, "email": "bush1508@phanmembanhang24h.com", "wp_role": "Subscriber"},
    {"username": "4k21jr", "wp_user_id": 7604, "email": "mattyawckml@chahcyrans.com", "wp_role": "Subscriber"},
    {"username": "50style.ru", "wp_user_id": 4624, "email": "fgdhhd@gmail.com", "wp_role": "AppFlicker Critic"},
    {"username": "5pljks", "wp_user_id": 7599, "email": "avijagtap@dmxs8.com", "wp_role": "Subscriber"},
    {"username": "78gt4s", "wp_user_id": 7070, "email": "azizxkill1@setxko.com", "wp_role": "Subscriber"},
    {"username": "7grl3j", "wp_user_id": 8005, "email": "alexwhitson@theking.id", "wp_role": "Subscriber"},
    {"username": "888starz_auOa", "wp_user_id": 8782, "email": "ytemqvjsoOa@problemno.shop", "wp_role": "JoulePepper Contributor"},
    {"username": "888starz_bqOa", "wp_user_id": 8884, "email": "jquloqoxdOa@problemno.shop", "wp_role": "JoulePepper Contributor"},
    {"username": "888starz_buOa", "wp_user_id": 8767, "email": "rjyjeyngeOa@problemno.shop", "wp_role": "JoulePepper Contributor"},
    {"username": "888starz_cdOa", "wp_user_id": 8778, "email": "vmeovaaglOa@problemno.shop", "wp_role": "JoulePepper Contributor"},
    {"username": "888starz_cfEl", "wp_user_id": 8121, "email": "bztagzwgnEl@skachat-na-android.com", "wp_role": "AppFlicker Critic"},
    {"username": "888starz_cfOa", "wp_user_id": 8880, "email": "yvuclwaevOa@problemno.shop", "wp_role": "JoulePepper Contributor"},
    {"username": "888starz_ckOa", "wp_user_id": 8886, "email": "cguuxulrcOa@problemno.shop", "wp_role": "JoulePepper Contributor"},
    {"username": "888starz_cqKr", "wp_user_id": 8661, "email": "vhelcuieoKr@igurant1.online", "wp_role": "JoulePepper Contributor"},
]

class Command(BaseCommand):
    help = "Bulk onboard WP users for risk evaluation"

    def handle(self, *args, **kwargs):
        count = 0
        for u in WP_USERS:
            eval_res = evaluate_registration(u["username"], u["email"])
            obj, created = UserOnboardingState.objects.update_or_create(
                wp_user_id=u["wp_user_id"],
                defaults={
                    "username": u["username"],
                    "email": u["email"],
                    "evaluation_status": eval_res["evaluation_status"],
                    "risk_score": eval_res["risk_score"],
                    "risk_reasons": eval_res["risk_reasons"],
                    "onboarding_stage": eval_res["onboarding_stage"],
                    "assigned_role": eval_res["assigned_role"],
                }
            )
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Successfully evaluated and onboarded {count} WP users."))
