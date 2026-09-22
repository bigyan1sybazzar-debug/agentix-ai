from django.db import models


# =====================================================================
# WORKBOOK 1 & 2: Registration, Email Verification & Progressive Asks
# =====================================================================

class UserOnboardingState(models.Model):
    """
    Workbook 1 & 2: User Onboarding, Risk Evaluation & Progressive Profiling.
    Tracks probationary roles, progressive asks (age, location, bio, avatar),
    and escalation status.
    """
    EVALUATION_CHOICES = [
        ("approved", "Approved"),
        ("flagged", "Flagged for Review"),
        ("rejected", "Rejected / High Risk"),
    ]

    STAGE_CHOICES = [
        ("registered", "Registered"),
        ("email_pending", "Email Pending"),
        ("progressive_asks", "Progressive Asks Incomplete"),
        ("completed", "Onboarding Complete"),
        ("escalated", "Escalated to Admin"),
    ]

    wp_user_id = models.IntegerField(unique=True, db_index=True)
    username = models.CharField(max_length=150)
    email = models.EmailField()
    email_verified = models.BooleanField(default=False)
    
    # Progressive Asks
    age = models.IntegerField(null=True, blank=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    avatar_completed = models.BooleanField(default=False)
    
    # Evaluation & Risk
    evaluation_status = models.CharField(max_length=30, choices=EVALUATION_CHOICES, default="approved")
    risk_score = models.FloatField(default=0.0)
    risk_reasons = models.TextField(blank=True, null=True)
    onboarding_stage = models.CharField(max_length=50, choices=STAGE_CHOICES, default="registered")
    
    # Role & Permissions
    assigned_role = models.CharField(max_length=50, default="subscriber_probationary")
    can_post = models.BooleanField(default=False)
    can_comment = models.BooleanField(default=False)
    can_vote = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_onboarding_states"
        ordering = ["-id"]

    def __str__(self):
        return f"User {self.username} ({self.assigned_role}, Stage: {self.onboarding_stage})"


# =====================================================================
# WORKBOOK 3: Content Participation, Creation & Moderation
# =====================================================================

class ContentSubmission(models.Model):
    """
    Workbook 3: Content Participation and Submission.
    Stores draft reviews, forum topics, and comments.
    """
    CONTENT_TYPES = [
        ("review", "Review Post"),
        ("forum_topic", "Forum Topic"),
        ("comment", "Comment / Reply"),
        ("poll", "Poll Submission"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted for Moderation"),
        ("approved", "Approved / Published"),
        ("flagged", "Flagged"),
        ("rejected", "Rejected"),
    ]

    wp_user_id = models.IntegerField(db_index=True)
    author_username = models.CharField(max_length=150)
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPES, default="review")
    title = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="submitted")
    assistance_applied = models.BooleanField(default=False)
    assistance_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content_submissions"
        ordering = ["-id"]

    def __str__(self):
        return f"[{self.content_type.upper()}] {self.title} by {self.author_username} ({self.status})"


class ModerationCase(models.Model):
    """
    Workbook 3: Moderation Reason Codes and Queue.
    """
    STATUS_CHOICES = [
        ("open", "Open / Pending"),
        ("resolved_approved", "Resolved - Approved"),
        ("resolved_rejected", "Resolved - Rejected"),
        ("escalated", "Escalated to Senior Moderator"),
    ]

    submission = models.ForeignKey(ContentSubmission, on_delete=models.CASCADE, related_name="moderation_cases")
    wp_user_id = models.IntegerField()
    reason_code = models.CharField(max_length=100)  # SPAM, HARASSMENT, OFF_TOPIC, UNVERIFIED_AUTHOR, POLICY_VIOLATION
    flagged_reason = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="open")
    moderator_notes = models.TextField(blank=True, null=True)
    resolved_by = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "moderation_cases"
        ordering = ["-id"]

    def __str__(self):
        return f"ModCase #{self.id}: {self.reason_code} on Submission #{self.submission_id} ({self.status})"


# =====================================================================
# WORKBOOK 4: Governance, Shared Audit & Reaction Rules
# =====================================================================

class GovernanceAuditLog(models.Model):
    """
    Workbook 4: Shared Audit Trail for all governance actions, validation checks,
    moderation decisions, and automated reactions.
    """
    ACTOR_TYPES = [
        ("user", "User"),
        ("system", "System Automation"),
        ("admin", "Admin / Chief of Staff"),
        ("agent", "Autonomous Agent"),
    ]

    actor_type = models.CharField(max_length=50, choices=ACTOR_TYPES, default="system")
    actor_id = models.CharField(max_length=150, blank=True, null=True)
    event_type = models.CharField(max_length=100, db_index=True)  # registration_eval, governance_check, moderation_action, reaction_fired
    action = models.CharField(max_length=100)
    result = models.CharField(max_length=50)  # allow, deny, escalate, flag, reaction_applied
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "governance_audit_logs"
        ordering = ["-id"]

    def __str__(self):
        return f"[{self.event_type}] {self.action} -> {self.result} by {self.actor_type}:{self.actor_id}"


# =====================================================================
# WORKBOOK 11: Identity Resolution, Vector Memory & Module Analytics
# =====================================================================

class IdentityCandidateLink(models.Model):
    """
    Workbook 11: Identity Resolution Model
    Maps local user representations across different SFPs/sites to global identities.
    """
    STATUS_CHOICES = [
        ("candidate", "Candidate"),
        ("review_candidate", "Review Candidate (70%-89%)"),
        ("high_confidence_candidate", "High Confidence Candidate (90%+)"),
        ("confirmed", "Confirmed Link"),
        ("rejected", "Rejected Link"),
    ]

    local_user_key = models.CharField(max_length=255, db_index=True)
    sfp_name = models.CharField(max_length=255, db_index=True)
    candidate_global_user_key = models.CharField(max_length=255, db_index=True)
    confidence_score = models.FloatField(default=0.0)
    link_reason = models.CharField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="candidate")
    reviewed_by = models.CharField(max_length=255, blank=True, null=True)
    review_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "identity_candidate_links"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.local_user_key} -> {self.candidate_global_user_key} ({self.status}, {self.confidence_score:.2f})"


class RetrievalDocument(models.Model):
    """
    Workbook 11: Retrieval Document Model
    Stores policies, transcripts, reviews, handbooks, precedents with vector memory status.
    """
    DOC_TYPES = [
        ("policy", "Policy"),
        ("transcript", "Transcript"),
        ("review", "Review"),
        ("handbook", "Handbook"),
        ("precedent", "Precedent"),
        ("general", "General"),
    ]

    VECTOR_STATUS_CHOICES = [
        ("pending", "Pending Embedding"),
        ("embedded", "Embedded"),
        ("failed", "Failed"),
    ]

    doc_key = models.CharField(max_length=255, unique=True)
    doc_type = models.CharField(max_length=50, choices=DOC_TYPES, default="general")
    sfp_name = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField()
    metadata_json = models.JSONField(default=dict, blank=True)
    vector_status = models.CharField(max_length=50, choices=VECTOR_STATUS_CHOICES, default="pending")
    embedding_json = models.JSONField(default=list, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "retrieval_documents"
        ordering = ["-id"]

    def __str__(self):
        return f"[{self.doc_type}] {self.title or self.doc_key} ({self.vector_status})"


class ModuleAnalyticsSnapshot(models.Model):
    """
    Workbook 11: Module Analytics Snapshot Model
    Tracks usage count, approval count, rejection count, and escalation rates.
    """
    module_key = models.CharField(max_length=255, db_index=True)
    sfp_name = models.CharField(max_length=255, db_index=True)
    usage_count = models.IntegerField(default=0)
    approval_count = models.IntegerField(default=0)
    rejection_count = models.IntegerField(default=0)
    escalation_count = models.IntegerField(default=0)
    notes = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "module_analytics_snapshots"
        ordering = ["-id"]

    @property
    def approval_rate(self):
        return (self.approval_count / self.usage_count) if self.usage_count else 0.0

    @property
    def escalation_rate(self):
        return (self.escalation_count / self.usage_count) if self.usage_count else 0.0

    def __str__(self):
        return f"{self.module_key} ({self.sfp_name}) - {self.usage_count} uses ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


# =====================================================================
# WORKBOOK 13: Review Post Media Assistant & Provenance
# =====================================================================

class MediaCandidate(models.Model):
    """
    Workbook 13: Media Candidate Model
    Stores discovered image candidates for review posts with validation & ranking scores.
    """
    CONTENT_TYPES = [
        ("film", "Film Poster"),
        ("tv", "TV Series Art"),
        ("game", "Video Game Cover"),
        ("album", "Music Album Cover"),
        ("book", "Book Cover"),
        ("thumbnail", "Thumbnail / Supporting Media"),
    ]

    VALIDATION_CHOICES = [
        ("pending", "Pending Validation"),
        ("approved", "Approved"),
        ("review_required", "Review Required"),
        ("rejected", "Rejected"),
    ]

    post_target_title = models.CharField(max_length=255, db_index=True)
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPES, default="film")
    candidate_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    source_url = models.URLField(max_length=1000)
    source_domain = models.CharField(max_length=255)
    width = models.IntegerField(default=0)
    height = models.IntegerField(default=0)
    aspect_ratio = models.CharField(max_length=50, default="1:1")
    quality_score = models.FloatField(default=0.0)
    rights_status = models.CharField(max_length=50, default="editorial_caution")
    validation_status = models.CharField(max_length=50, choices=VALIDATION_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "media_candidates"
        ordering = ["-quality_score", "-id"]

    def __str__(self):
        return f"{self.post_target_title} - {self.title} (Score: {self.quality_score:.1f}, {self.validation_status})"


class MediaProvenanceLog(models.Model):
    """
    Workbook 13: Media Provenance Log Model
    Maintains the full audit trail and governance metadata for attached media.
    """
    candidate = models.ForeignKey(MediaCandidate, on_delete=models.CASCADE, related_name="provenance_logs")
    source_url = models.URLField(max_length=1000)
    source_domain = models.CharField(max_length=255)
    provenance_status = models.CharField(max_length=50, default="verified")
    review_required = models.BooleanField(default=False)
    assistance_applied = models.BooleanField(default=True)
    autonomous_origin = models.BooleanField(default=False)
    agent_package_id = models.CharField(max_length=100, blank=True, null=True)
    notes = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "media_provenance_logs"
        ordering = ["-id"]

    def __str__(self):
        return f"Provenance #{self.id} for Candidate {self.candidate_id} ({self.provenance_status})"


class ReviewPostDraft(models.Model):
    """
    Workbook 13: Review Post Draft & Packaging Model
    Represents posts ready to be packaged for WordPress with full Learnami Post-Meta.
    """
    MODE_CHOICES = [
        ("manual", "Manual Mode"),
        ("assisted", "Assisted Mode"),
        ("autonomous", "Autonomous Mode"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("packaged", "Packaged for WordPress"),
        ("synced", "Synced to WordPress"),
    ]

    title = models.CharField(max_length=255)
    content_type = models.CharField(max_length=50, default="film")
    mode = models.CharField(max_length=50, choices=MODE_CHOICES, default="assisted")
    content_body = models.TextField(blank=True)
    selected_media = models.ForeignKey(MediaCandidate, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="draft")
    wordpress_post_id = models.IntegerField(null=True, blank=True)
    package_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "review_post_drafts"
        ordering = ["-id"]

    def __str__(self):
        return f"[{self.mode.upper()}] {self.title} ({self.status})"


# =====================================================================
# Automation Task Log
# =====================================================================

class AutomationTaskLog(models.Model):
    """
    Orchestration and Execution log for automated pipelines
    """
    pipeline_name = models.CharField(max_length=100)
    status = models.CharField(max_length=50, default="success")
    summary = models.CharField(max_length=255)
    items_processed = models.IntegerField(default=0)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "automation_task_logs"
        ordering = ["-id"]

    def __str__(self):
        return f"[{self.pipeline_name}] {self.status} - {self.summary} ({self.created_at.strftime('%H:%M:%S')})"


# =====================================================================
# WORKBOOK 5, 7, 8, 9, 10: Policy Registry, Hierarchy, Orchestration & SFPs
# =====================================================================

class PolicyRule(models.Model):
    """Workbook 5: Policy Registry Rule Definition."""
    policy_key = models.CharField(max_length=150, unique=True)
    policy_type = models.CharField(max_length=100) # registration, moderation, governance, privacy
    platform_context = models.CharField(max_length=100, default="global")
    action_type = models.CharField(max_length=100, blank=True, null=True)
    rule_config = models.JSONField(default=dict, blank=True)
    priority = models.IntegerField(default=1)
    enabled = models.BooleanField(default=True)
    version = models.CharField(max_length=20, default="v1")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "policy_rules"
        ordering = ["priority", "-id"]

    def __str__(self):
        return f"Policy [{self.policy_key}] ({self.policy_type}, enabled={self.enabled})"


class PolicyChangeRequest(models.Model):
    """Workbook 7: Hierarchical Policy Review & Approval Request."""
    policy_key = models.CharField(max_length=150)
    requested_by = models.CharField(max_length=150)
    proposed_config = models.JSONField(default=dict, blank=True)
    justification = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, default="pending") # pending, approved, rejected
    reviewed_by = models.CharField(max_length=150, blank=True, null=True)
    review_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "policy_change_requests"
        ordering = ["-id"]


class ReleaseReadinessCheck(models.Model):
    """Workbook 7: Release-Readiness Gate Criteria & Audit."""
    scope_type = models.CharField(max_length=100) # sfp, module, core
    scope_key = models.CharField(max_length=150)
    requested_by = models.CharField(max_length=150, blank=True, null=True)
    status = models.CharField(max_length=50, default="passed") # passed, failed, blocked
    score = models.FloatField(default=100.0)
    checks_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "release_readiness_checks"
        ordering = ["-id"]


class OrchestrationRule(models.Model):
    """Workbook 9: DB-Driven Event Orchestration Rule."""
    rule_key = models.CharField(max_length=150, unique=True)
    event_type = models.CharField(max_length=150, db_index=True)
    source_layer = models.CharField(max_length=100, blank=True, null=True)
    target_layer = models.CharField(max_length=100)
    target_actor = models.CharField(max_length=150, blank=True, null=True)
    conditions = models.JSONField(default=dict, blank=True)
    priority = models.IntegerField(default=1)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orchestration_rules"
        ordering = ["priority", "-id"]


class OrchestrationEventLog(models.Model):
    """Workbook 8: Operational Event Pipeline Audit Log."""
    event_type = models.CharField(max_length=150, db_index=True)
    source_actor = models.CharField(max_length=150, blank=True, null=True)
    target_layer = models.CharField(max_length=100, blank=True, null=True)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=50, default="dispatched")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orchestration_event_logs"
        ordering = ["-id"]


class PolicySimulationResult(models.Model):
    """Workbook 8: Sandbox Policy Impact Simulation Output."""
    simulation_name = models.CharField(max_length=200)
    policy_key = models.CharField(max_length=150)
    requested_by = models.CharField(max_length=150, blank=True, null=True)
    proposed_config = models.JSONField(default=dict, blank=True)
    sample_context = models.JSONField(default=dict, blank=True)
    result_summary = models.JSONField(default=dict, blank=True)
    passed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "policy_simulation_results"
        ordering = ["-id"]


class SystemConflict(models.Model):
    """Workbook 8: Cross-layer / Cross-SFP Policy Conflict Tracker."""
    conflict_type = models.CharField(max_length=150)
    severity = models.CharField(max_length=50, default="medium") # low, medium, high, critical
    description = models.TextField()
    status = models.CharField(max_length=50, default="open") # open, resolved, ignored
    reviewed_by = models.CharField(max_length=150, blank=True, null=True)
    review_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "system_conflicts"
        ordering = ["-id"]


class ReplayLog(models.Model):
    """Workbook 9: Event Replay & Backtest Audit Execution."""
    replay_name = models.CharField(max_length=200)
    event_type = models.CharField(max_length=150)
    source_layer = models.CharField(max_length=100, blank=True, null=True)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=50, default="completed")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "replay_logs"
        ordering = ["-id"]


class ReviewCycle(models.Model):
    """Workbook 9: Strategic Periodic Audit & Compliance Review Cycle."""
    cycle_type = models.CharField(max_length=100) # governance, moderation, identity, privacy
    requested_by = models.CharField(max_length=150, blank=True, null=True)
    status = models.CharField(max_length=50, default="completed")
    findings_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "review_cycles"
        ordering = ["-id"]


class SFPRegistry(models.Model):
    """Workbook 9 & 10: Single Feature Platform (SFP) Capability Registry."""
    sfp_key = models.CharField(max_length=100, unique=True)
    sfp_name = models.CharField(max_length=200)
    capabilities_json = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=50, default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sfp_registries"
        ordering = ["sfp_key"]

    def __str__(self):
        return f"SFP [{self.sfp_key}] - {self.sfp_name}"


# =====================================================================
# WORKBOOK 12: Privacy Boundaries, Operational Runbooks & Production Blueprint
# =====================================================================

class PrivacyAccessLog(models.Model):
    """Workbook 12: Data Access & Scope Access Audit Log."""
    requester_role = models.CharField(max_length=150)
    data_class = models.CharField(max_length=150) # cross_site_memory, user_pii, moderation_history, identity_links
    target_key = models.CharField(max_length=255, blank=True, null=True)
    decision = models.CharField(max_length=50, default="allowed") # allowed, masked, restricted, denied
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "privacy_access_logs"
        ordering = ["-id"]

    def __str__(self):
        return f"[{self.data_class}] {self.requester_role} -> {self.decision}"


class ConsentRecord(models.Model):
    """Workbook 12: Cross-Site User Consent & Preference Record."""
    global_user_key = models.CharField(max_length=255, db_index=True)
    consent_type = models.CharField(max_length=150) # cross_site_memory, data_sharing, analytics
    granted = models.BooleanField(default=True)
    source_sfp = models.CharField(max_length=150, blank=True, null=True)
    evidence = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "consent_records"
        ordering = ["-id"]

    def __str__(self):
        return f"Consent for {self.global_user_key}: {self.consent_type}={self.granted}"


class RunbookExecution(models.Model):
    """Workbook 12: Operational Runbook Execution Trail."""
    runbook_key = models.CharField(max_length=150) # policy_error_detected, moderation_surge, queue_backup, outage_recovery
    triggered_by = models.CharField(max_length=150, blank=True, null=True)
    status = models.CharField(max_length=50, default="running") # running, completed, failed
    notes = models.TextField(blank=True, null=True)
    steps_completed = models.JSONField(default=list, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "runbook_executions"
        ordering = ["-id"]

    def __str__(self):
        return f"Runbook [{self.runbook_key}] (#{self.id}) - {self.status}"


class SystemBlueprintSnapshot(models.Model):
    """Workbook 12: System Production Architecture Snapshot."""
    snapshot_name = models.CharField(max_length=200)
    summary = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "system_blueprint_snapshots"
        ordering = ["-id"]

    def __str__(self):
        return f"Blueprint Snapshot: {self.snapshot_name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

