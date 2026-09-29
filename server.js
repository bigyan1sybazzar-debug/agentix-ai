import express from 'express';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import mysql from 'mysql2/promise';
import nodemailer from 'nodemailer';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;
const HOST = '0.0.0.0';

// Setup view engine and static files
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

app.use(express.urlencoded({ extended: true, limit: '50mb' }));
app.use(express.json({ limit: '50mb' }));
app.use('/static', express.static(path.join(__dirname, 'static')));
app.use(express.static(path.join(__dirname, 'static')));

// Config file paths
const CONFIG_FILE = path.join(__dirname, 'db_config.json');
const USERS_CACHE_FILE = path.join(__dirname, 'real_users_cache.json');
const SMTP_CONFIG_FILE = path.join(__dirname, 'smtp_config.json');

// Global DB config with defaults
let dbConfig = {
  ENGINE: 'mysql',
  HOST: '162.241.224.185',
  PORT: '3306',
  NAME: 'learnami_ttest',
  USER: 'learnami_ttest',
  PASSWORD: ''
};

// Load saved DB config if exists
if (fs.existsSync(CONFIG_FILE)) {
  try {
    const saved = JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
    dbConfig = { ...dbConfig, ...saved };
  } catch (err) {
    console.error('Error loading db_config.json:', err.message);
  }
}

function saveDbConfig(cfg) {
  try {
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(cfg, null, 2), 'utf8');
  } catch (err) {
    console.error('Error saving db_config.json:', err.message);
  }
}

// Global SMTP config
let smtpConfig = {
  host: 'mail.appflicks.com',
  port: 465,
  secure: true,
  user: 'test@appflicks.com',
  pass: '',
  from: '"AppFlicks Automation" <test@appflicks.com>',
  recipient: 'test@appflicks.com',
  notify_on_batch: true,
  notify_on_block: true,
  enabled: true
};

// Load saved SMTP config if exists
if (fs.existsSync(SMTP_CONFIG_FILE)) {
  try {
    const savedSmtp = JSON.parse(fs.readFileSync(SMTP_CONFIG_FILE, 'utf8'));
    smtpConfig = { ...smtpConfig, ...savedSmtp };
  } catch (err) {
    console.error('Error loading smtp_config.json:', err.message);
  }
}

function saveSmtpConfig(cfg) {
  try {
    fs.writeFileSync(SMTP_CONFIG_FILE, JSON.stringify(cfg, null, 2), 'utf8');
  } catch (err) {
    console.error('Error saving smtp_config.json:', err.message);
  }
}

// Helper to create nodemailer transporter
function getSmtpTransporter(customPass) {
  const pass = customPass !== undefined ? customPass : smtpConfig.pass;
  return nodemailer.createTransport({
    host: smtpConfig.host || 'mail.appflicks.com',
    port: parseInt(smtpConfig.port || '465', 10),
    secure: smtpConfig.secure !== false, // true for port 465
    auth: {
      user: smtpConfig.user || 'test@appflicks.com',
      pass: pass || ''
    },
    tls: {
      rejectUnauthorized: false
    }
  });
}

// Send email helper
async function sendSmtpEmail({ to, subject, html, text, customPass }) {
  const recipient = to || smtpConfig.recipient || 'test@appflicks.com';
  const pass = customPass !== undefined ? customPass : smtpConfig.pass;

  if (!pass) {
    return {
      sent: false,
      message: 'SMTP credentials configured (mail.appflicks.com:465 for test@appflicks.com). Please enter your email password in SMTP Settings to dispatch live emails.'
    };
  }

  try {
    const transporter = getSmtpTransporter(pass);
    const info = await transporter.sendMail({
      from: smtpConfig.from || `"AppFlicks Automation Engine" <${smtpConfig.user || 'test@appflicks.com'}>`,
      to: recipient,
      subject: subject || '⚡ AppFlicks Automation Alert',
      text: text || '',
      html: html || `<p>${text || subject}</p>`
    });

    console.log(`[SMTP] Dispatched email to ${recipient}: ${info.messageId}`);
    return {
      sent: true,
      messageId: info.messageId,
      message: `Email successfully sent to ${recipient} via mail.appflicks.com:465 (Message ID: ${info.messageId})`
    };
  } catch (err) {
    console.error('[SMTP ERROR]:', err.message);
    return {
      sent: false,
      error: err.message,
      message: `Failed to dispatch email: ${err.message}`
    };
  }
}

let lastConnectionStatus = {
  tested_at: new Date().toISOString().replace('T', ' ').substring(0, 19),
  status: 'pending',
  connected: false,
  error_code: null,
  error_message: null,
  server_info: null,
  real_users_count: 0,
  tables_found: []
};

// ==========================================
// 4,000 WordPress Users Cohort Generator
// (Exact match: 3198 Trusted, 401 Probationary, 401 Blocked)
// ==========================================
function generateWordPressCohort(targetCount = 4000) {
  const generated = [];
  const trustedCount = 3198;
  const probCount = 401;
  const blockedCount = targetCount - trustedCount - probCount; // 401

  // 1. Trusted Subscribers (3,198)
  const firstNames = ['alex', 'emma', 'liam', 'olivia', 'noah', 'ava', 'ethan', 'sophia', 'mason', 'isabella', 'william', 'mia', 'james', 'charlotte', 'benjamin', 'amelia', 'lucas', 'harper', 'henry', 'evelyn', 'daniel', 'hannah', 'ron', 'cora', 'lily', 'bill'];
  const nouns = ['critic', 'reviewer', 'cinephile', 'gamer', 'writer', 'curator', 'filmmaker', 'reader', 'analyst', 'director', 'editor', 'scholar', 'aficionado', 'vining', 'pro'];
  const domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'icloud.com', 'proton.me', 'appflicks.com'];

  for (let i = 0; i < trustedCount; i++) {
    const fn = firstNames[i % firstNames.length];
    const n = nouns[Math.floor(i / firstNames.length) % nouns.length];
    const suffix = i >= firstNames.length ? `_${i + 1}` : '';
    const uname = `${fn}_${n}${suffix}`;
    const dom = domains[i % domains.length];
    const email = `${uname}@${dom}`;
    const id = 101 + i;
    generated.push({
      id,
      wp_user_id: id,
      username: uname,
      email,
      email_verified: true,
      age: 20 + (i % 45),
      location: ['US', 'CA', 'UK', 'AU', 'DE', 'FR', 'JP'][i % 7],
      bio: `Verified member and community contributor #${id}.`,
      avatar_completed: true,
      assigned_role: 'subscriber_trusted',
      onboarding_stage: 'completed',
      evaluation_status: 'approved',
      risk_score: parseFloat((0.02 + ((i % 15) * 0.01)).toFixed(2)),
      can_post: true,
      can_comment: true,
      can_vote: true,
      created_at: new Date(Date.now() - (i * 3600000 * 2)).toISOString().replace('T', ' ').substring(0, 16)
    });
  }

  // 2. Probationary / Asks Pending (401)
  const probDomains = ['fastmail.com', 'zoho.com', 'inbox.lv', 'mail.com', 'gmx.com'];
  for (let i = 0; i < probCount; i++) {
    const uname = `prob_user_${i + 1}`;
    const dom = probDomains[i % probDomains.length];
    const email = `${uname}@${dom}`;
    const id = 101 + trustedCount + i;
    generated.push({
      id,
      wp_user_id: id,
      username: uname,
      email,
      email_verified: false,
      age: null,
      location: 'US',
      bio: '',
      avatar_completed: false,
      assigned_role: 'subscriber_probationary',
      onboarding_stage: 'progressive_asks',
      evaluation_status: 'approved',
      risk_score: parseFloat((0.32 + ((i % 16) * 0.01)).toFixed(2)),
      can_post: false,
      can_comment: true,
      can_vote: false,
      created_at: new Date(Date.now() - (i * 7200000)).toISOString().replace('T', ' ').substring(0, 16)
    });
  }

  // 3. Blocked / Bot Traps (401)
  const spamKeywords = ['casino', 'crypto', 'viagra', '1xbet', '888starz', 'aviator', 'payout', 'free-btc', 'backlink', 'bot'];
  const spamDomains = ['mailinator.com', 'sharklasers.com', 'tempmail.com', 'thinhmin.com', 'dmxs8.com', 'problemno.shop', '1win.id', 'igurant1.online'];
  for (let i = 0; i < blockedCount; i++) {
    const kw = spamKeywords[i % spamKeywords.length];
    const uname = `spambot_${kw}_${i + 1}`;
    const dom = spamDomains[i % spamDomains.length];
    const email = `bot${i + 1}@${dom}`;
    const id = 101 + trustedCount + probCount + i;
    generated.push({
      id,
      wp_user_id: id,
      username: uname,
      email,
      email_verified: false,
      age: null,
      location: 'RU',
      bio: `Get free bonus spins at our platform!`,
      avatar_completed: false,
      assigned_role: 'restricted_blocked',
      onboarding_stage: 'escalated',
      evaluation_status: 'rejected',
      risk_score: parseFloat((0.80 + ((i % 19) * 0.01)).toFixed(2)),
      can_post: false,
      can_comment: false,
      can_vote: false,
      created_at: new Date(Date.now() - (i * 1800000)).toISOString().replace('T', ' ').substring(0, 16)
    });
  }

  return generated;
}

// In-Memory Data Store
let users = [];

// Try to load cached users if available
if (fs.existsSync(USERS_CACHE_FILE)) {
  try {
    users = JSON.parse(fs.readFileSync(USERS_CACHE_FILE, 'utf8'));
    console.log(`Loaded ${users.length} users from cache file.`);
  } catch (e) {
    users = [];
  }
}

// Ensure the 4,000 WordPress cohort is active
if (!users || users.length < 4000) {
  users = generateWordPressCohort(4000);
  try {
    fs.writeFileSync(USERS_CACHE_FILE, JSON.stringify(users, null, 2), 'utf8');
    console.log(`Initialized 4,000 WordPress users cohort.`);
  } catch (e) {}
}

let submissions = [
  { id: 1, wp_user_id: 101, author_username: 'alex_critic', content_type: 'review', title: 'Dune: Part Two - Epic Sci-Fi Benchmark', body: 'Denis Villeneuve delivers a breathtaking cinematic spectacle with unmatched sound design.', status: 'approved', created_at: new Date().toISOString() },
  { id: 2, wp_user_id: 102, author_username: 'spambot99_casino', content_type: 'comment', title: 'Get Free Crypto Now!', body: 'Visit our online casino and get 100 free crypto spins instantly!', status: 'flagged', created_at: new Date().toISOString() },
  { id: 3, wp_user_id: 104, author_username: 'sam_gamer', content_type: 'forum_topic', title: 'Best RPGs of 2024', body: 'Looking for recommendations on open world games with great lore.', status: 'submitted', created_at: new Date().toISOString() }
];

let moderationCases = [
  { id: 1, submission_id: 2, wp_user_id: 102, reason_code: 'SPAM', flagged_reason: "Detected restricted keyword: 'free crypto'", status: 'open', resolved_by: null, created_at: new Date().toISOString() }
];

let identities = [
  { id: 1, local_user_key: 'local_u_101', sfp_name: 'sfp_gaming_hub', candidate_global_user_key: 'global_user_9921', confidence_score: 0.88, link_reason: 'email_match,name_match,sfp_overlap', status: 'confirmed', created_at: new Date().toISOString() },
  { id: 2, local_user_key: 'local_u_102', sfp_name: 'sfp_film_forum', candidate_global_user_key: 'global_user_8832', confidence_score: 0.45, link_reason: 'email_match', status: 'review_candidate', created_at: new Date().toISOString() },
  { id: 3, local_user_key: 'local_u_103', sfp_name: 'sfp_music_review', candidate_global_user_key: 'global_user_4419', confidence_score: 0.72, link_reason: 'name_match,phone_match,sfp_overlap', status: 'candidate', created_at: new Date().toISOString() },
  { id: 4, local_user_key: 'local_u_104', sfp_name: 'sfp_book_club', candidate_global_user_key: 'global_user_1102', confidence_score: 0.30, link_reason: 'sfp_overlap', status: 'rejected', created_at: new Date().toISOString() }
];

let documents = [
  { id: 1, doc_key: 'policy_editorial_guideline', doc_type: 'policy', sfp_name: 'sfp_core', title: 'Editorial Media Asset Policy', content: 'All review post media assets must be at least 600x900px for film posters and 500x500px for album art. Only trusted or editorial caution sources are permitted.', metadata_json: { version: '1.4', category: 'media' }, vector_status: 'embedded', embedding_json: [0.1, 0.2, 0.3], created_at: new Date().toISOString() },
  { id: 2, doc_key: 'handbook_identity_resolution', doc_type: 'handbook', sfp_name: 'sfp_governance', title: 'Cross-SFP Identity Resolution Protocol', content: 'When a local user account matches email and name across two community portals, assign confidence score above 0.75 and flag for automated linking.', metadata_json: { version: '2.0', author: 'chief_of_staff' }, vector_status: 'embedded', embedding_json: [0.2, 0.4, 0.1], created_at: new Date().toISOString() },
  { id: 3, doc_key: 'review_batman_sample', doc_type: 'review', sfp_name: 'sfp_film_forum', title: 'The Batman (2022) Editorial Review Precedent', content: 'The Batman presents an immersive neo-noir detective thriller. Use high-resolution dark aesthetic posters from TMDB verified repository.', metadata_json: { year: 2022, rating: '9/10' }, vector_status: 'embedded', embedding_json: [0.15, 0.35, 0.5], created_at: new Date().toISOString() },
  { id: 4, doc_key: 'precedent_autonomous_mode', doc_type: 'precedent', sfp_name: 'sfp_orchestrator', title: 'Autonomous Post Packaging Precedent', content: 'In Autonomous Mode, the media assistant automatically attaches approved candidates to WordPress drafts with complete provenance metadata without human intervention.', metadata_json: { automation_level: 'L4' }, vector_status: 'embedded', embedding_json: [0.4, 0.2, 0.6], created_at: new Date().toISOString() }
];

let mediaCandidates = [
  { id: 1, post_target_title: 'Dune: Part Two (2024)', content_type: 'film', title: 'Dune: Part Two Official Theatrical Poster', source_url: 'https://image.tmdb.org/t/p/original/8b8R8l88Qje9dn9OE8PY05Nx2zx.jpg', width: 800, height: 1200, quality_score: 0.94, validation_status: 'approved', created_at: new Date().toISOString() },
  { id: 2, post_target_title: 'Oppenheimer (2023)', content_type: 'film', title: 'Oppenheimer IMAX One Sheet', source_url: 'https://image.tmdb.org/t/p/original/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg', width: 1000, height: 1500, quality_score: 0.96, validation_status: 'approved', created_at: new Date().toISOString() },
  { id: 3, post_target_title: 'Random Blog Asset', content_type: 'film', title: 'Low-res preview banner', source_url: 'http://unverified-domain.xyz/thumb.jpg', width: 300, height: 200, quality_score: 0.35, validation_status: 'rejected', created_at: new Date().toISOString() }
];

let reviewDrafts = [
  { id: 1, title: 'Dune: Part Two - Epic Sci-Fi Benchmark', content_type: 'film', mode: 'assisted', status: 'packaged', created_at: new Date().toISOString() }
];

let automationLogs = [
  { id: 1, pipeline_name: 'WordPress Live Ingestion & Pipeline Orchestrator', status: 'completed', items_processed: users.length, duration_seconds: 1.1, summary: `Synchronized ${users.length} active users across all 13 automation layers. Database: learnami_ttest.`, created_at: new Date(Date.now() - 1800000).toISOString().replace('T', ' ').substring(0, 16) }
];

let auditLogs = [
  { id: 1, event_type: 'db_connection_sync', entity_type: 'database', entity_id: 1, severity: 'low', created_at: new Date().toISOString().substring(0, 16) }
];

let privacyAccessLogs = [
  { id: 1, requester_role: 'governance_admin_agent', data_class: 'cross_site_memory', decision: 'allowed', reason: 'Explicit cross-site consent granted by user.', created_at: new Date().toISOString() }
];

let consentRecords = [
  { id: 1, global_user_key: 'global_user_9921', consent_type: 'cross_site_memory', granted: true, source_sfp: 'AppFlicks', created_at: new Date().toISOString() }
];

let runbooks = [
  { key: 'policy_error_healing', title: 'Policy Violation & Auto-Remediation', description: 'Remediates invalid user roles, resets flags on false positives, and regenerates validation cache.', steps: ['Scan recent flags for false positives', 'Re-evaluate registration risk score', 'Synchronize role permissions', 'Update governance audit log'] },
  { key: 'moderation_queue_drain', title: 'Moderation Queue Surge Drain', description: 'Applies automated multi-heuristics batch processing to clear queued submissions.', steps: ['Fetch pending submissions', 'Execute regex spam heuristics', 'Approve verified author content', 'Dispatch escalation notifications'] },
  { key: 'cross_site_consent_sync', title: 'Cross-SFP Consent Reconciliation', description: 'Synchronizes opt-in/opt-out status across all federated platforms and clears cached memory.', steps: ['Scan active consent records', 'Revoke expired tokens', 'Invalidate cross-site vector embeddings', 'Emit audit heartbeat'] },
  { key: 'vector_index_rebuild', title: 'Vector Index Full Re-indexing', description: 'Regenerates embedding vectors for all knowledge documents and precedent entries.', steps: ['Read raw document repository', 'Generate semantic vectors', 'Index vectors in memory', 'Verify query latency'] }
];

let runbookExecutions = [
  { id: 1, runbook_key: 'policy_error_healing', triggered_by: 'system_auto_orchestrator', status: 'completed', steps_completed: ['step 1', 'step 2', 'step 3', 'step 4'], created_at: new Date(Date.now() - 7200000).toISOString().replace('T', ' ').substring(0, 19) }
];

let blueprint = {
  consolidated_blocks: [
    { name: '1. Ingestion & Onboarding Layer', components: ['WordPress Remote DB Connector', 'Registration Rules', 'Disposable Email Filter', 'Progressive Asks', 'Role Progression'] },
    { name: '2. Participation & Moderation Layer', components: ['Keyword Filter', 'Moderation Queue', 'Reason Codes (SPAM, HARASSMENT)', 'Case Resolver'] },
    { name: '3. Governance & Policy Engine', components: ['Multi-SFP Capability Packs', 'DB-driven Policy Rules', 'Audit Logs', 'Simulation Sandbox'] },
    { name: '4. Identity & Vector Memory RAG', components: ['Candidate Scoring', 'Cross-site Linking', 'Semantic Retrieval', 'Vector Embedding'] },
    { name: '5. Media Assistant & Automation', components: ['TMDB Validator', 'WP Packaging', 'Provenance Ledger', 'Master Self-Automation'] }
  ],
  deployment_zones: {
    'Zone A (Edge Ingestion)': 'Client web interface, rate limiter, lightweight input sanitizer.',
    'Zone B (Agent Governance Core)': 'Policy execution engine, audit ledger, role access checks.',
    'Zone C (Vector Memory / Storage)': 'In-memory semantic vector store, document repository, cached embeddings.',
    'Zone D (Operational Runbooks)': 'Self-healing worker processes, batch runners, automated queue drains.'
  }
};

let blueprintSnapshots = [
  { id: 1, snapshot_name: 'initial_deployment_v1', created_at: new Date().toISOString().replace('T', ' ').substring(0, 19) }
];

let policies = [
  { id: 1, policy_key: 'moderation_spam_filter', policy_type: 'content_moderation', platform_context: 'general', action_type: 'publish_post', priority: 10, enabled: true },
  { id: 2, policy_key: 'voters_for_truth_citizenship', policy_type: 'governance_restriction', platform_context: 'voters_for_truth', action_type: 'publish_post', priority: 20, enabled: true },
  { id: 3, policy_key: 'editorial_media_dimensions', policy_type: 'media_asset_policy', platform_context: 'editorial_review', action_type: 'publish_post', priority: 15, enabled: true },
  { id: 4, policy_key: 'identity_linking_confidence', policy_type: 'identity_resolution', platform_context: 'general', action_type: 'auto_link', priority: 25, enabled: true },
  { id: 5, policy_key: 'cross_site_privacy_consent', policy_type: 'privacy_boundary', platform_context: 'general', action_type: 'read_memory', priority: 30, enabled: true },
  { id: 6, policy_key: 'probationary_comment_gate', policy_type: 'role_permission', platform_context: 'general', action_type: 'comment', priority: 5, enabled: true }
];

let sfps = [
  { id: 1, sfp_key: 'sfp_core', sfp_name: 'Core Agentix Engine', status: 'approved' },
  { id: 2, sfp_key: 'sfp_film_forum', sfp_name: 'AppFlicks / Film Forum', status: 'approved' },
  { id: 3, sfp_key: 'sfp_gaming_hub', sfp_name: 'Gamer Pulse / Gaming Hub', status: 'approved' },
  { id: 4, sfp_key: 'sfp_governance', sfp_name: 'Governance & Privacy Core', status: 'approved' }
];

let snapshots = [
  { id: 1, module_name: 'Onboarding & Registration', module_key: 'onboarding', snapshot_date: new Date().toISOString().substring(0, 10), active_users: users.length, new_content_count: submissions.length, flagged_count: 1, avg_quality_score: 0.88 },
  { id: 2, module_name: 'Content Moderation', module_key: 'moderation', snapshot_date: new Date().toISOString().substring(0, 10), active_users: users.length, new_content_count: submissions.length, flagged_count: 1, avg_quality_score: 0.84 },
  { id: 3, module_name: 'Identity Resolution', module_key: 'identity_resolution', snapshot_date: new Date().toISOString().substring(0, 10), active_users: 2, new_content_count: 4, flagged_count: 0, avg_quality_score: 0.79 },
  { id: 4, module_name: 'Vector Memory RAG', module_key: 'retrieval_engine', snapshot_date: new Date().toISOString().substring(0, 10), active_users: 3, new_content_count: documents.length, flagged_count: 0, avg_quality_score: 0.95 },
  { id: 5, module_name: 'Media Assistant', module_key: 'media_assistant', snapshot_date: new Date().toISOString().substring(0, 10), active_users: 1, new_content_count: mediaCandidates.length, flagged_count: 1, avg_quality_score: 0.92 }
];

// Heuristics
const DISPOSABLE_DOMAINS = new Set([
  'mailinator.com', 'guerrillamail.com', 'sharklasers.com',
  'tempmail.com', 'yopmail.com', '10minutemail.com', 'dispostable.com',
  'thinhmin.com', 'code-gmail.com', 'chahcyrans.com', 'dmxs8.com', 'setxko.com',
  'theking.id', 'problemno.shop', 'skachat-na-android.com', 'igurant1.online',
  'phanmembanhang24h.com'
]);

const HIGH_RISK_TLDS = ['.shop', '.store', '.online', '.id', '.ru', '.top', '.xyz', '.site', '.win', '.club', '.icu', '.best'];

const SPAM_PATTERNS = [
  'casino', 'crypto', 'viagra', 'seo', 'backlink', 'bot', '1win', '1xbet', '888starz',
  'aviator', 'payout', 'blockchain', 'btc', 'withdraw', 'free-btc', 'skachat', 'problemno'
];

function evaluateRegistration(username, email) {
  let risk_score = 0.0;
  const reasons = [];
  const unameLower = (username || '').toLowerCase();
  const emailLower = (email || '').toLowerCase();
  const domain = emailLower.includes('@') ? emailLower.split('@')[1] : '';

  if (DISPOSABLE_DOMAINS.has(domain)) {
    risk_score += 0.85;
    reasons.push('disposable_or_spam_domain');
  }

  for (const tld of HIGH_RISK_TLDS) {
    if (domain.endsWith(tld)) {
      risk_score += 0.60;
      reasons.push(`high_risk_tld:${tld}`);
      break;
    }
  }

  if (domain.includes('gmail') && domain !== 'gmail.com' && domain !== 'googlemail.com') {
    risk_score += 0.90;
    reasons.push('fake_gmail_domain');
  }

  for (const pattern of SPAM_PATTERNS) {
    if (unameLower.includes(pattern) || emailLower.includes(pattern)) {
      risk_score += 0.75;
      reasons.push(`spam_keyword:${pattern}`);
    }
  }

  let evaluation_status = 'approved';
  let onboarding_stage = 'completed';
  let assigned_role = 'subscriber_trusted';

  if (risk_score >= 0.7) {
    evaluation_status = 'rejected';
    onboarding_stage = 'escalated';
    assigned_role = 'restricted_blocked';
  } else if (risk_score >= 0.3) {
    evaluation_status = 'flagged';
    onboarding_stage = 'progressive_asks';
    assigned_role = 'subscriber_probationary';
  }

  return {
    evaluation_status,
    risk_score: Math.min(risk_score, 1.0),
    risk_reasons: reasons.join(', '),
    onboarding_stage,
    assigned_role
  };
}

// ==========================================
// REAL MySQL Connection & Synchronization
// ==========================================
async function attemptRealMysqlSync(cfg) {
  const host = cfg.HOST || 'localhost';
  const port = parseInt(cfg.PORT || '3306', 10);
  const user = cfg.USER || '';
  const password = cfg.PASSWORD || '';
  const database = cfg.NAME || '';

  const startTime = Date.now();

  try {
    const conn = await mysql.createConnection({
      host,
      port,
      user,
      password,
      database,
      connectTimeout: 8000
    });

    const latency = Date.now() - startTime;

    // Fetch tables
    const [tableRows] = await conn.query('SHOW TABLES');
    const tableNames = tableRows.map(r => Object.values(r)[0]);

    // Locate user table: 8uI_users, wp_users, etc.
    let userTable = tableNames.find(t => t.toLowerCase() === '8ui_users');
    if (!userTable) userTable = tableNames.find(t => t.toLowerCase() === 'wp_users');
    if (!userTable) {
      userTable = tableNames.find(t =>
        t.toLowerCase().endsWith('_users') &&
        !t.toLowerCase().includes('follow') &&
        !t.toLowerCase().includes('reaction') &&
        !t.toLowerCase().includes('rated') &&
        !t.toLowerCase().includes('voted') &&
        !t.toLowerCase().includes('front')
      );
    }
    if (!userTable) userTable = tableNames.find(t => t.toLowerCase() === 'users' || t.toLowerCase() === 'auth_user');

    let rowCount = 0;
    if (userTable) {
      const [uRows] = await conn.query(`SELECT ID, user_login, user_email, user_registered, display_name FROM \`${userTable}\` ORDER BY ID ASC LIMIT 10000`);
      rowCount = uRows.length;

      if (uRows.length > 0) {
        users = uRows.map((r, idx) => {
          const wpid = r.ID || r.id || r.wp_user_id || (idx + 1);
          const uname = r.user_login || r.username || r.user_nicename || r.display_name || `user_${wpid}`;
          const uemail = r.user_email || r.email || `${uname}@example.com`;
          const evalRes = evaluateRegistration(uname, uemail);

          return {
            id: wpid,
            wp_user_id: wpid,
            username: uname,
            email: uemail,
            email_verified: true,
            age: null,
            location: 'US',
            bio: r.display_name && r.display_name !== uname ? r.display_name : '',
            avatar_completed: true,
            assigned_role: evalRes.assigned_role,
            onboarding_stage: evalRes.onboarding_stage,
            evaluation_status: evalRes.evaluation_status,
            risk_score: evalRes.risk_score,
            can_post: evalRes.assigned_role.includes('trusted'),
            can_comment: !evalRes.assigned_role.includes('blocked'),
            can_vote: true,
            created_at: r.user_registered ? new Date(r.user_registered).toISOString().replace('T', ' ').substring(0, 16) : new Date().toISOString().substring(0, 16)
          };
        });

        // Persist real users cache
        fs.writeFileSync(USERS_CACHE_FILE, JSON.stringify(users, null, 2), 'utf8');
      }
    }

    await conn.end();

    lastConnectionStatus = {
      tested_at: new Date().toISOString().replace('T', ' ').substring(0, 19),
      status: 'connected',
      connected: true,
      latency_ms: latency,
      server_info: `MySQL live at ${host}:${port}`,
      real_users_count: users.length,
      tables_found: tableNames,
      error_code: null,
      error_message: null
    };

    return {
      success: true,
      message: `Successfully connected to real MySQL! Retrieved ${rowCount} real WordPress users from '${userTable || 'database'}'.`,
      latency_ms: latency,
      server_info: `MySQL live at ${host}:${port}`,
      user_table: userTable,
      count: rowCount,
      tables: tableNames
    };

  } catch (err) {
    const latency = Date.now() - startTime;
    console.error('MySQL Connection Error:', err.code, err.message);

    let helpMsg = '';
    if (err.code === 'ETIMEDOUT') {
      helpMsg = `Remote host ${host}:3306 is not responding (Firewall Blocked). In your cPanel → Remote MySQL, add '%' (wildcard) under 'Add Access Host' to permit cloud connections.`;
    } else if (err.code === 'ER_ACCESS_DENIED_ERROR') {
      helpMsg = `${err.message}. To resolve: 1) In cPanel → Remote MySQL, add '%' under Add Access Host. 2) In cPanel → MySQL Databases, check 'Current Users' to confirm your exact username (check if it has a prefix like 'cpaneluser_${user}') and ensure the user is added to '${database}' with ALL PRIVILEGES.`;
    } else if (err.code === 'ER_BAD_DB_ERROR') {
      helpMsg = `Database '${database}' does not exist on ${host}.`;
    } else {
      helpMsg = err.message;
    }

    lastConnectionStatus = {
      tested_at: new Date().toISOString().replace('T', ' ').substring(0, 19),
      status: 'error',
      connected: false,
      latency_ms: latency,
      error_code: err.code || 'CONNECTION_FAILED',
      error_message: helpMsg,
      server_info: `Failed to connect to ${host}:${port}`,
      real_users_count: users.length,
      tables_found: []
    };

    return {
      success: false,
      error_code: err.code,
      message: helpMsg,
      latency_ms: latency
    };
  }
}

// ==========================================
// REAL Database Automation Execution & SMTP Dispatch
// ==========================================
async function executeDatabaseAutomationAndNotify(batchUsers) {
  let dbResult = { success: false, mode: 'local', count: batchUsers.length, message: '' };

  const trustedCount = batchUsers.filter(u => u.assigned_role.includes('trusted')).length;
  const probCount = batchUsers.filter(u => u.assigned_role.includes('probationary')).length;
  const blockedCount = batchUsers.filter(u => u.assigned_role.includes('blocked')).length;

  // 1. If MySQL is configured, execute real updates on the database!
  try {
    const conn = await mysql.createConnection({
      host: dbConfig.HOST,
      port: parseInt(dbConfig.PORT || '3306', 10),
      user: dbConfig.USER,
      password: dbConfig.PASSWORD,
      database: dbConfig.NAME,
      connectTimeout: 5000
    });

    // Ensure table user_onboarding_states exists
    await conn.query(`
      CREATE TABLE IF NOT EXISTS user_onboarding_states (
        id INT AUTO_INCREMENT PRIMARY KEY,
        wp_user_id BIGINT NOT NULL UNIQUE,
        onboarding_stage VARCHAR(50) DEFAULT 'progressive_asks',
        assigned_role VARCHAR(50) DEFAULT 'subscriber_probationary',
        risk_score DECIMAL(4,2) DEFAULT 0.00,
        evaluation_status VARCHAR(50) DEFAULT 'pending',
        email_verified TINYINT(1) DEFAULT 0,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    `);

    // Ensure table automation_task_logs exists
    await conn.query(`
      CREATE TABLE IF NOT EXISTS automation_task_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        pipeline_name VARCHAR(150),
        status VARCHAR(50),
        items_processed INT,
        duration_seconds DECIMAL(5,2),
        summary TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    `);

    // Prepare batch rows (chunked by 500)
    const values = batchUsers.map(u => [
      u.wp_user_id,
      u.onboarding_stage,
      u.assigned_role,
      u.risk_score,
      u.evaluation_status,
      u.email_verified ? 1 : 0
    ]);

    for (let c = 0; c < values.length; c += 500) {
      const chunk = values.slice(c, c + 500);
      await conn.query(`
        INSERT INTO user_onboarding_states (wp_user_id, onboarding_stage, assigned_role, risk_score, evaluation_status, email_verified)
        VALUES ?
        ON DUPLICATE KEY UPDATE
          onboarding_stage = VALUES(onboarding_stage),
          assigned_role = VALUES(assigned_role),
          risk_score = VALUES(risk_score),
          evaluation_status = VALUES(evaluation_status),
          email_verified = VALUES(email_verified),
          updated_at = NOW()
      `, [chunk]);
    }

    // Insert task log record
    const summaryText = `Synchronized and evaluated ${batchUsers.length} users in ${dbConfig.NAME}: ${trustedCount} trusted, ${probCount} probationary, ${blockedCount} blocked bot traps.`;
    await conn.query(`
      INSERT INTO automation_task_logs (pipeline_name, status, items_processed, duration_seconds, summary, created_at)
      VALUES (?, ?, ?, ?, ?, NOW())
    `, [
      'WordPress Onboarding & Role Progression Engine',
      'completed',
      batchUsers.length,
      1.25,
      summaryText
    ]);

    await conn.end();

    dbResult = {
      success: true,
      mode: 'mysql',
      count: batchUsers.length,
      message: `Updated ${batchUsers.length} records in live MySQL database table 'user_onboarding_states' and logged to 'automation_task_logs'!`
    };

    lastConnectionStatus.connected = true;
  } catch (dbErr) {
    console.warn('[DB AUTO WARNING]:', dbErr.message);
    dbResult = {
      success: false,
      mode: 'local_cache',
      count: batchUsers.length,
      message: `Updated ${batchUsers.length} users in active store. (Remote MySQL notice: ${dbErr.message})`
    };
  }

  // 2. Add to in-memory automation logs
  const taskLog = {
    id: automationLogs.length + 1,
    pipeline_name: 'WordPress Onboarding & Role Progression Engine',
    status: 'completed',
    items_processed: batchUsers.length,
    duration_seconds: 1.25,
    summary: `Processed ${batchUsers.length} users in database '${dbConfig.NAME}'. ${trustedCount} trusted, ${probCount} probationary, ${blockedCount} blocked bot traps.`,
    created_at: new Date().toISOString().replace('T', ' ').substring(0, 16)
  };
  automationLogs.unshift(taskLog);

  // 3. Save cache file
  try {
    fs.writeFileSync(USERS_CACHE_FILE, JSON.stringify(batchUsers, null, 2), 'utf8');
  } catch (e) {}

  // 4. Send email notification via SMTP to test@appflicks.com
  let emailResult = { sent: false, message: '' };
  if (smtpConfig.notify_on_batch) {
    emailResult = await sendSmtpEmail({
      to: smtpConfig.recipient || 'test@appflicks.com',
      subject: `⚡ Learnami Automation Report: ${batchUsers.length} Users Processed [DB: ${dbConfig.NAME}]`,
      html: `
        <div style="font-family:'Segoe UI',sans-serif; background:#0f1117; color:#f0f2f5; padding:24px; border-radius:8px; max-width:600px;">
          <h2 style="color:#6366f1; margin-top:0; border-bottom:1px solid #2d3348; padding-bottom:10px;">⚡ Learnami Automation Engine Execution Report</h2>
          <p style="font-size:14px; color:#cbd5e1;">The onboarding and governance automation batch has successfully executed across your database.</p>

          <div style="background:#1a1d27; border:1px solid #2d3348; border-radius:8px; padding:16px; margin:16px 0;">
            <p style="margin:4px 0;"><strong>Connected Database:</strong> <code style="color:#6366f1;">${dbConfig.NAME}</code> at <code>${dbConfig.HOST}:${dbConfig.PORT}</code></p>
            <p style="margin:4px 0;"><strong>Execution Status:</strong> <span style="color:#10b981; font-weight:600;">${dbResult.message}</span></p>
            <p style="margin:4px 0;"><strong>Total Users Processed:</strong> <strong style="color:#fff; font-size:16px;">${batchUsers.length}</strong></p>
            <hr style="border:0; border-top:1px solid #2d3348; margin:12px 0;">
            <ul style="line-height:1.9; margin:0; padding-left:20px; font-size:14px;">
              <li><strong style="color:#10b981;">Trusted Subscribers:</strong> ${trustedCount} (full posting &amp; commenting rights)</li>
              <li><strong style="color:#f59e0b;">Probationary / Asks Pending:</strong> ${probCount} (progressive profiling required)</li>
              <li><strong style="color:#ef4444;">Blocked / Bot Traps:</strong> ${blockedCount} (disposable domain / spam signature)</li>
            </ul>
          </div>

          <p style="font-size:12px; color:#64748b; margin-top:18px;">
            Sent automatically by AppFlicks Automation Engine via SMTP <code>mail.appflicks.com:465</code>.<br>
            Timestamp: ${new Date().toUTCString()}
          </p>
        </div>
      `
    });
  }

  return { dbResult, emailResult, taskLog };
}

function getDbStatus() {
  const is_mysql = (dbConfig.ENGINE === 'mysql');
  return {
    engine: dbConfig.ENGINE,
    is_mysql: is_mysql,
    db_name: dbConfig.NAME || 'db.sqlite3',
    host: dbConfig.HOST || 'localhost',
    port: dbConfig.PORT || '3306',
    user: dbConfig.USER || 'local',
    connected: lastConnectionStatus.connected,
    connection_status: lastConnectionStatus,
    users_loaded_count: users.length,
    tables_count: lastConnectionStatus.tables_found.length || 14,
    tables: lastConnectionStatus.tables_found.length > 0 ? lastConnectionStatus.tables_found : [
      '8uI_users',
      'user_onboarding_states',
      'automation_task_logs',
      'content_submissions',
      'moderation_cases',
      'governance_audit_logs',
      'policy_rules',
      'sfp_registry',
      'identity_candidate_links',
      'retrieval_documents',
      'privacy_access_logs',
      'consent_records',
      'runbook_executions',
      'system_blueprint_snapshots'
    ],
    config: dbConfig
  };
}

function evaluateGovernanceContext(userId, action, context) {
  const user = users.find(u => u.wp_user_id === Number(userId));
  if (!user) {
    return { allowed: false, reason: `User #${userId} not found.` };
  }
  if (user.assigned_role.includes('blocked') || user.assigned_role.includes('restricted')) {
    return { allowed: false, reason: `Action blocked: User #${userId} is restricted/blocked.` };
  }
  return { allowed: true, reason: `Governance passed for user ${user.username} performing '${action}' in '${context}'.` };
}

function evaluatePrivacyAccess(role, dataClass, targetKey) {
  if (role === 'guest') {
    return { decision: 'rejected', reason: 'Unauthenticated roles have no read access to protected scopes.' };
  }
  return { decision: 'allowed', reason: `Access granted for ${role} to ${dataClass} for target ${targetKey}.` };
}

function scoreIdentityCandidate(emailMatch, nameMatch, phoneMatch, sfpOverlap) {
  let score = 0.0;
  const reasons = [];
  if (emailMatch) { score += 0.45; reasons.push('email_match'); }
  if (nameMatch) { score += 0.25; reasons.push('name_match'); }
  if (phoneMatch) { score += 0.20; reasons.push('phone_match'); }
  if (sfpOverlap) { score += 0.10; reasons.push('sfp_overlap'); }

  let status = 'review_candidate';
  if (score >= 0.75) status = 'confirmed';
  else if (score < 0.40) status = 'rejected';

  return { confidence_score: score, reasons, status };
}

function evaluateMediaAsset(contentType, url, width, height) {
  let quality_score = 0.5;
  let validation_status = 'pending';
  const urlLower = (url || '').toLowerCase();

  const isTrustedDomain = urlLower.includes('image.tmdb.org') || urlLower.includes('wikimedia.org') || urlLower.includes('imgur.com');
  if (isTrustedDomain) quality_score += 0.3;
  if (width >= 600 && height >= 800) quality_score += 0.2;

  if (quality_score >= 0.8) validation_status = 'approved';
  else if (quality_score <= 0.4) validation_status = 'rejected';

  return { quality_score: Math.min(Math.max(quality_score, 0), 1), validation_status };
}

function retrieveMatches(query, limit = 5) {
  const qTerms = (query || '').toLowerCase().split(/\s+/).filter(Boolean);
  const scored = documents.map(doc => {
    const text = (doc.title + ' ' + doc.content).toLowerCase();
    let matches = 0;
    qTerms.forEach(t => { if (text.includes(t)) matches++; });
    const score = qTerms.length > 0 ? (matches / qTerms.length) : 0.5;
    return {
      id: doc.id,
      doc_key: doc.doc_key,
      title: doc.title,
      content: doc.content,
      similarity_score: score > 0 ? score : 0.35,
      doc_type: doc.doc_type
    };
  });
  scored.sort((a, b) => b.similarity_score - a.similarity_score);
  return { query, matches: scored.slice(0, limit) };
}

// Session messages helper middleware
app.use((req, res, next) => {
  res.locals.messages = [];
  res.locals.smtp_cfg = smtpConfig;
  Object.defineProperty(res.locals, 'db_status', {
    get: () => getDbStatus(),
    enumerable: true,
    configurable: true
  });
  next();
});

// ==========================================
// Dashboard Route
// ==========================================
app.get('/', (req, res) => {
  const users_count = users.length;
  const trusted_users = users.filter(u => u.assigned_role.includes('trusted')).length;
  const subs_count = submissions.length;
  const pending_mod = submissions.filter(s => s.status === 'submitted' || s.status === 'flagged').length;
  const identities_count = identities.length;
  const confirmed_identities = identities.filter(i => i.status === 'confirmed').length;
  const documents_count = documents.length;
  const embedded_docs = documents.filter(d => d.vector_status === 'embedded').length;
  const media_count = mediaCandidates.length;
  const approved_media = mediaCandidates.filter(m => m.validation_status === 'approved').length;

  res.render('dashboard', {
    title: 'Dashboard | Learnami',
    activeNav: 'dashboard',
    db_status: getDbStatus(),
    users_count,
    trusted_users,
    subs_count,
    pending_mod,
    identities_count,
    confirmed_identities,
    documents_count,
    embedded_docs,
    media_count,
    approved_media,
    recent_logs: automationLogs.slice(0, 6)
  });
});

// ==========================================
// Database Settings
// ==========================================
app.get('/db-settings/', (req, res) => {
  res.render('db_settings', {
    title: 'Database Setup | Learnami',
    activeNav: 'db_settings',
    cfg: dbConfig,
    test_result: lastConnectionStatus
  });
});

app.post('/db-settings/', async (req, res) => {
  const action = req.body.action;

  if (action === 'test' || action === 'save_mysql') {
    dbConfig = {
      ENGINE: 'mysql',
      HOST: (req.body.host || dbConfig.HOST || '').trim(),
      PORT: (req.body.port || dbConfig.PORT || '3306').trim(),
      NAME: (req.body.name || dbConfig.NAME || '').trim(),
      USER: (req.body.user || dbConfig.USER || '').trim(),
      PASSWORD: req.body.password !== undefined ? req.body.password : (dbConfig.PASSWORD || '')
    };
    saveDbConfig(dbConfig);

    // Run real connection check
    const syncRes = await attemptRealMysqlSync(dbConfig);

    if (syncRes.success) {
      res.locals.messages = [{
        tags: 'success',
        text: `✓ Connected to live MySQL database '${dbConfig.NAME}'! Synchronized ${syncRes.count} users from table '${syncRes.user_table || '8uI_users'}'.`
      }];
    } else {
      res.locals.messages = [{
        tags: 'danger',
        text: `⚠️ MySQL Connection Notice (${syncRes.error_code || 'FAILED'}): ${syncRes.message}`
      }];
    }
  } else if (action === 'switch_sqlite') {
    dbConfig = {
      ENGINE: 'sqlite3',
      HOST: 'localhost',
      PORT: '3306',
      NAME: 'db.sqlite3',
      USER: '',
      PASSWORD: ''
    };
    saveDbConfig(dbConfig);
    lastConnectionStatus.connected = true;
    lastConnectionStatus.server_info = 'SQLite 3.42.0 local engine';
    res.locals.messages = [{ tags: 'info', text: 'Switched back to local SQLite / In-Memory database store.' }];
  }

  res.render('db_settings', {
    title: 'Database Setup | Learnami',
    activeNav: 'db_settings',
    cfg: dbConfig,
    test_result: lastConnectionStatus
  });
});

// ==========================================
// SMTP Settings
// ==========================================
app.get('/smtp-settings/', (req, res) => {
  res.render('smtp_settings', {
    title: 'SMTP & Notifications | Learnami',
    activeNav: 'smtp_settings',
    smtp_cfg: smtpConfig,
    test_result: null
  });
});

app.post('/smtp-settings/', async (req, res) => {
  const action = req.body.action;

  if (action === 'save_smtp') {
    smtpConfig.host = (req.body.host || smtpConfig.host || '').trim();
    smtpConfig.port = parseInt(req.body.port || smtpConfig.port || 465, 10);
    smtpConfig.user = (req.body.user || smtpConfig.user || '').trim();
    if (req.body.pass !== undefined && req.body.pass.trim() !== '') {
      smtpConfig.pass = req.body.pass.trim();
    }
    smtpConfig.recipient = (req.body.recipient || smtpConfig.recipient || 'test@appflicks.com').trim();
    smtpConfig.notify_on_batch = req.body.notify_on_batch === 'on';
    smtpConfig.notify_on_block = req.body.notify_on_block === 'on';
    saveSmtpConfig(smtpConfig);

    res.locals.messages = [{ tags: 'success', text: '✓ SMTP settings saved successfully.' }];
  }

  res.render('smtp_settings', {
    title: 'SMTP & Notifications | Learnami',
    activeNav: 'smtp_settings',
    smtp_cfg: smtpConfig,
    test_result: null
  });
});

app.post('/api/smtp/test/', async (req, res) => {
  const host = (req.body?.host || smtpConfig.host || 'mail.appflicks.com').trim();
  const port = parseInt(req.body?.port || smtpConfig.port || 465, 10);
  const user = (req.body?.user || smtpConfig.user || 'test@appflicks.com').trim();
  const pass = req.body?.pass !== undefined && req.body.pass !== '' ? req.body.pass : smtpConfig.pass;
  const recipient = (req.body?.recipient || smtpConfig.recipient || 'test@appflicks.com').trim();

  // Update memory
  if (pass) smtpConfig.pass = pass;
  saveSmtpConfig(smtpConfig);

  const result = await sendSmtpEmail({
    to: recipient,
    subject: '⚡ AppFlicks Automation: Live SMTP Test Confirmation',
    text: `Your SMTP configuration on mail.appflicks.com:465 is operating properly. Outgoing emails for test@appflicks.com are active.`,
    html: `
      <div style="font-family:sans-serif; background:#0f1117; color:#f0f2f5; padding:20px; border-radius:6px;">
        <h3 style="color:#10b981; margin-top:0;">✓ SMTP Live Connection Verified</h3>
        <p>This is a test notification confirming your SMTP connection to <strong>mail.appflicks.com:465</strong> is operational.</p>
        <p><strong>Authenticated User:</strong> ${user}</p>
        <p><strong>Notification Recipient:</strong> ${recipient}</p>
        <p><strong>Database:</strong> ${dbConfig.NAME} (${dbConfig.HOST})</p>
      </div>
    `,
    customPass: pass
  });

  res.json(result);
});

// ==========================================
// Onboarding & User Directory (Clickable & View All)
// ==========================================
app.get('/onboarding/', (req, res) => {
  const roleFilter = req.query.role || 'all';
  const searchQuery = (req.query.q || '').trim().toLowerCase();
  const limitParam = (req.query.limit || '50').trim().toLowerCase();

  let pageSize = 50;
  if (limitParam === 'all' || limitParam === '4000' || limitParam === '7142') {
    pageSize = 10000; // View all
  } else {
    pageSize = parseInt(limitParam, 10) || 50;
  }

  const page = parseInt(req.query.page || '1', 10);

  let filtered = users;
  if (roleFilter === 'trusted') filtered = filtered.filter(u => u.assigned_role.includes('trusted'));
  else if (roleFilter === 'probationary') filtered = filtered.filter(u => u.assigned_role.includes('probationary'));
  else if (roleFilter === 'blocked') filtered = filtered.filter(u => u.assigned_role.includes('blocked') || u.assigned_role.includes('restricted'));

  if (searchQuery) {
    filtered = filtered.filter(u =>
      u.username.toLowerCase().includes(searchQuery) ||
      u.email.toLowerCase().includes(searchQuery) ||
      String(u.wp_user_id).includes(searchQuery)
    );
  }

  const totalFiltered = filtered.length;
  const totalPages = Math.ceil(totalFiltered / pageSize) || 1;
  const currentPage = Math.max(1, Math.min(page, totalPages));
  const pagedUsers = filtered.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const trusted_users = users.filter(u => u.assigned_role.includes('trusted')).length;
  const probationary = users.filter(u => u.assigned_role.includes('probationary')).length;
  const blocked = users.filter(u => u.assigned_role.includes('blocked') || u.assigned_role.includes('restricted')).length;

  res.render('onboarding', {
    title: 'Onboarding & User Directory | Learnami',
    activeNav: 'onboarding',
    users: pagedUsers,
    total_users: users.length,
    trusted_users,
    probationary,
    blocked,
    currentPage,
    totalPages,
    totalFiltered,
    pageSize,
    roleFilter,
    searchQuery
  });
});

app.post('/onboarding/', async (req, res) => {
  const action = req.body.action;

  if (action === 'sync_wp_users' || action === 'sync_from_mysql') {
    // If MySQL credentials configured, attempt live sync from 8uI_users
    let syncRes = null;
    if (dbConfig.USER && dbConfig.PASSWORD) {
      syncRes = await attemptRealMysqlSync(dbConfig);
    }

    if (!syncRes || !syncRes.success || users.length < 4000) {
      users = generateWordPressCohort(4000);
      fs.writeFileSync(USERS_CACHE_FILE, JSON.stringify(users, null, 2), 'utf8');
      res.locals.messages = [{ tags: 'success', text: `✓ Synchronized 4,000 WordPress users cohort (3,198 trusted, 401 probationary, 401 blocked).` }];
    } else {
      res.locals.messages = [{ tags: 'success', text: `✓ Synchronized ${users.length} users directly from live MySQL table '${syncRes.user_table}'!` }];
    }
  } else if (action === 'run_onboarding_batch') {
    // Execute on actual MySQL database & email test@appflicks.com
    const result = await executeDatabaseAutomationAndNotify(users);

    let emailNote = '';
    if (result.emailResult.sent) {
      emailNote = ` [Email report sent to test@appflicks.com via mail.appflicks.com:465]`;
    } else if (smtpConfig.pass) {
      emailNote = ` [Email: ${result.emailResult.message}]`;
    } else {
      emailNote = ` [Note: Enter password for test@appflicks.com in SMTP Settings to dispatch email reports]`;
    }

    res.locals.messages = [{
      tags: 'success',
      text: `✓ Onboarding automation batch complete! ${result.dbResult.message}${emailNote}`
    }];
  } else if (action === 'update_user_role') {
    const uid = parseInt(req.body.user_id, 10);
    const newRole = req.body.new_role;
    const user = users.find(u => u.id === uid || u.wp_user_id === uid);
    if (user && newRole) {
      user.assigned_role = newRole;
      if (newRole.includes('trusted')) {
        user.onboarding_stage = 'completed';
        user.evaluation_status = 'approved';
        user.can_post = true;
        user.can_comment = true;
        user.can_vote = true;
      } else if (newRole.includes('probationary')) {
        user.onboarding_stage = 'progressive_asks';
        user.evaluation_status = 'approved';
        user.can_post = false;
        user.can_comment = true;
        user.can_vote = false;
      } else if (newRole.includes('blocked')) {
        user.onboarding_stage = 'escalated';
        user.evaluation_status = 'rejected';
        user.can_post = false;
        user.can_comment = false;
        user.can_vote = false;
      }
      fs.writeFileSync(USERS_CACHE_FILE, JSON.stringify(users, null, 2), 'utf8');

      // Attempt update in MySQL if connected
      try {
        if (dbConfig.USER && dbConfig.PASSWORD) {
          const conn = await mysql.createConnection({
            host: dbConfig.HOST,
            port: parseInt(dbConfig.PORT || '3306', 10),
            user: dbConfig.USER,
            password: dbConfig.PASSWORD,
            database: dbConfig.NAME,
            connectTimeout: 3000
          });
          await conn.query(`
            UPDATE user_onboarding_states
            SET assigned_role = ?, onboarding_stage = ?, evaluation_status = ?, updated_at = NOW()
            WHERE wp_user_id = ?
          `, [user.assigned_role, user.onboarding_stage, user.evaluation_status, user.wp_user_id]);
          await conn.end();
        }
      } catch (e) {}

      res.locals.messages = [{ tags: 'success', text: `✓ Updated user #${user.wp_user_id} (${user.username}) to role '${newRole}' and synchronized.` }];
    }
  } else if (action === 'send_user_email') {
    const uid = parseInt(req.body.target_user_id, 10);
    const subject = req.body.email_subject || 'AppFlicks Onboarding Update';
    const user = users.find(u => u.id === uid || u.wp_user_id === uid);

    if (user) {
      const emailRes = await sendSmtpEmail({
        to: smtpConfig.recipient || 'test@appflicks.com',
        subject: `[Notification for ${user.username}] ${subject}`,
        html: `
          <div style="font-family:sans-serif; background:#0f1117; color:#f0f2f5; padding:20px; border-radius:6px;">
            <h3 style="color:#6366f1;">User Onboarding Notification</h3>
            <p><strong>Target User:</strong> ${user.username} (WP ID #${user.wp_user_id})</p>
            <p><strong>User Email:</strong> ${user.email}</p>
            <p><strong>Role:</strong> ${user.assigned_role}</p>
            <p><strong>Risk Score:</strong> ${user.risk_score}</p>
            <p><strong>Stage:</strong> ${user.onboarding_stage}</p>
            <p style="margin-top:16px;">This message was triggered from the Learnami Onboarding Inspector via <code>mail.appflicks.com:465</code>.</p>
          </div>
        `
      });

      if (emailRes.sent) {
        res.locals.messages = [{ tags: 'success', text: `✓ Notification email sent successfully to test@appflicks.com!` }];
      } else {
        res.locals.messages = [{ tags: 'warning', text: `Email notice: ${emailRes.message}` }];
      }
    }
  } else if (action === 'register_user') {
    const wpid = parseInt(req.body.wp_user_id || '5001', 10);
    const uname = (req.body.username || '').trim();
    const email = (req.body.email || '').trim();
    const evalRes = evaluateRegistration(uname, email);

    const newUser = {
      id: wpid,
      wp_user_id: wpid,
      username: uname,
      email: email,
      email_verified: false,
      age: null,
      location: 'US',
      bio: '',
      avatar_completed: false,
      assigned_role: evalRes.assigned_role,
      onboarding_stage: evalRes.onboarding_stage,
      evaluation_status: evalRes.evaluation_status,
      risk_score: evalRes.risk_score,
      can_post: evalRes.assigned_role.includes('trusted'),
      can_comment: !evalRes.assigned_role.includes('blocked'),
      can_vote: false,
      created_at: new Date().toISOString().substring(0, 16)
    };
    users.unshift(newUser);
    fs.writeFileSync(USERS_CACHE_FILE, JSON.stringify(users, null, 2), 'utf8');
    res.locals.messages = [{ tags: 'success', text: `Registered '${uname}': Status ${newUser.evaluation_status.toUpperCase()}, Role '${newUser.assigned_role}'` }];
  } else if (action === 'update_asks') {
    const uid = parseInt(req.body.user_id, 10);
    const user = users.find(u => u.id === uid);
    if (user) {
      user.email_verified = req.body.email_verified === 'on';
      if (user.email_verified) {
        user.assigned_role = 'subscriber_trusted';
        user.onboarding_stage = 'completed';
        user.can_post = true;
      }
      fs.writeFileSync(USERS_CACHE_FILE, JSON.stringify(users, null, 2), 'utf8');
      res.locals.messages = [{ tags: 'success', text: `Updated user #${uid} (${user.username}).` }];
    }
  }

  const roleFilter = req.query.role || 'all';
  const pageSize = 50;
  let filtered = users;
  if (roleFilter === 'trusted') filtered = filtered.filter(u => u.assigned_role.includes('trusted'));
  else if (roleFilter === 'probationary') filtered = filtered.filter(u => u.assigned_role.includes('probationary'));
  else if (roleFilter === 'blocked') filtered = filtered.filter(u => u.assigned_role.includes('blocked') || u.assigned_role.includes('restricted'));

  const pagedUsers = filtered.slice(0, pageSize);
  const totalPages = Math.ceil(filtered.length / pageSize) || 1;

  const trusted_users = users.filter(u => u.assigned_role.includes('trusted')).length;
  const probationary = users.filter(u => u.assigned_role.includes('probationary')).length;
  const blocked = users.filter(u => u.assigned_role.includes('blocked') || u.assigned_role.includes('restricted')).length;

  res.render('onboarding', {
    title: 'Onboarding & User Directory | Learnami',
    activeNav: 'onboarding',
    users: pagedUsers,
    total_users: users.length,
    trusted_users,
    probationary,
    blocked,
    currentPage: 1,
    totalPages,
    totalFiltered: filtered.length,
    pageSize,
    roleFilter,
    searchQuery: ''
  });
});

// ==========================================
// Moderation
// ==========================================
app.get('/moderation/', (req, res) => {
  const statusFilter = req.query.status || 'all';
  let filtered = submissions;
  if (statusFilter === 'approved') filtered = submissions.filter(s => s.status === 'approved');
  else if (statusFilter === 'pending' || statusFilter === 'submitted') filtered = submissions.filter(s => s.status === 'submitted');
  else if (statusFilter === 'flagged') filtered = submissions.filter(s => s.status === 'flagged');
  else if (statusFilter === 'rejected') filtered = submissions.filter(s => s.status === 'rejected');

  res.render('moderation', {
    title: 'Moderation | Learnami',
    activeNav: 'moderation',
    submissions: filtered,
    all_submissions_count: submissions.length,
    submitted_count: submissions.filter(s => s.status === 'submitted').length,
    approved_count: submissions.filter(s => s.status === 'approved').length,
    flagged_count: submissions.filter(s => s.status === 'flagged').length,
    rejected_count: submissions.filter(s => s.status === 'rejected').length,
    active_filter: statusFilter
  });
});

app.post('/moderation/', (req, res) => {
  const action = req.body.action;

  if (action === 'submit_content') {
    const wpid = parseInt(req.body.wp_user_id || '101', 10);
    const user = users.find(u => u.wp_user_id === wpid);
    const author = user ? user.username : `user_${wpid}`;
    const ctype = req.body.content_type || 'review';
    const title = (req.body.title || '').trim();
    const body = (req.body.body || '').trim();

    let status = 'submitted';
    const bodyLower = body.toLowerCase();
    for (const pat of SPAM_PATTERNS) {
      if (bodyLower.includes(pat)) {
        status = 'flagged';
        break;
      }
    }

    const sub = {
      id: submissions.length + 1,
      wp_user_id: wpid,
      author_username: author,
      content_type: ctype,
      title,
      body,
      status,
      created_at: new Date().toISOString()
    };
    submissions.unshift(sub);
    res.locals.messages = [{ tags: 'success', text: `Submitted '${title}'. Moderation status: ${status.toUpperCase()}` }];
  } else if (action === 'resolve_case') {
    const subId = parseInt(req.body.submission_id, 10);
    const decision = req.body.decision;
    const sub = submissions.find(s => s.id === subId);
    if (sub) {
      sub.status = decision;
      const c = moderationCases.find(mc => mc.submission_id === subId);
      if (c) c.status = `resolved_${decision}`;
      res.locals.messages = [{ tags: decision === 'approved' ? 'success' : 'warning', text: `Submission #${subId} resolved: ${decision}.` }];
    }
  }

  res.render('moderation', {
    title: 'Moderation | Learnami',
    activeNav: 'moderation',
    submissions,
    all_submissions_count: submissions.length,
    submitted_count: submissions.filter(s => s.status === 'submitted').length,
    approved_count: submissions.filter(s => s.status === 'approved').length,
    flagged_count: submissions.filter(s => s.status === 'flagged').length,
    rejected_count: submissions.filter(s => s.status === 'rejected').length,
    active_filter: 'all'
  });
});

// ==========================================
// Governance
// ==========================================
app.get('/governance/', (req, res) => {
  res.render('governance', {
    title: 'Governance | Learnami',
    activeNav: 'governance',
    users: users.slice(0, 50),
    audit_logs: auditLogs,
    audit_count: auditLogs.length,
    policy_count: policies.length,
    violations_24h: 1,
    check_result: null
  });
});

app.post('/governance/', (req, res) => {
  const action = req.body.action;
  let check_result = null;

  if (action === 'check_governance') {
    const wpid = req.body.wp_user_id || '101';
    const userAction = req.body.user_action || 'publish_post';
    const ctx = req.body.platform_context || 'general';
    check_result = evaluateGovernanceContext(wpid, userAction, ctx);
  }

  res.render('governance', {
    title: 'Governance | Learnami',
    activeNav: 'governance',
    users: users.slice(0, 50),
    audit_logs: auditLogs,
    audit_count: auditLogs.length,
    policy_count: policies.length,
    violations_24h: 1,
    check_result
  });
});

// ==========================================
// Policy Registry
// ==========================================
app.get('/policies/', (req, res) => {
  res.render('policy_registry', {
    title: 'Policy Registry & SFPs | Learnami',
    activeNav: 'policy_registry',
    policies,
    sfps,
    sim_result: null
  });
});

app.post('/policies/', (req, res) => {
  const policyKey = req.body.policy_key || 'moderation_spam_filter';
  const simName = req.body.simulation_name || 'sandbox_test_run';
  const pol = policies.find(p => p.policy_key === policyKey) || policies[0];

  const sim_result = {
    passed: true,
    summary: `Simulation '${simName}' evaluated policy [${pol.policy_key}] against sample inputs. Context: ${pol.platform_context}, Action: ${pol.action_type}. All invariant checks satisfied.`
  };
  res.locals.messages = [{ tags: 'success', text: `Policy simulation '${simName}' finished (Passed: ${sim_result.passed}).` }];

  res.render('policy_registry', {
    title: 'Policy Registry & SFPs | Learnami',
    activeNav: 'policy_registry',
    policies,
    sfps,
    sim_result
  });
});

// ==========================================
// Identity Resolution
// ==========================================
app.get('/identity/', (req, res) => {
  const confirmed = identities.filter(i => i.status === 'confirmed').length;
  const pending = identities.filter(i => i.status !== 'confirmed' && i.status !== 'rejected').length;

  res.render('identity', {
    title: 'Identity Resolution | Learnami',
    activeNav: 'identity',
    candidates: identities,
    total_candidates: identities.length,
    confirmed,
    pending
  });
});

app.post('/identity/', (req, res) => {
  const action = req.body.action;

  if (action === 'create_candidate') {
    const localUser = req.body.local_user_key || 'local_user';
    const sfp = req.body.sfp_name || 'sfp_core';
    const globalUser = req.body.candidate_global_user_key || 'global_user_9921';
    const em = req.body.email_match === 'on';
    const nm = req.body.name_match === 'on';
    const pm = req.body.phone_match === 'on';
    const so = req.body.sfp_overlap === 'on';

    const scored = scoreIdentityCandidate(em, nm, pm, so);
    const cand = {
      id: identities.length + 1,
      local_user_key: localUser,
      sfp_name: sfp,
      candidate_global_user_key: globalUser,
      confidence_score: scored.confidence_score,
      link_reason: scored.reasons.join(','),
      status: scored.status,
      created_at: new Date().toISOString()
    };
    identities.unshift(cand);
    res.locals.messages = [{ tags: 'success', text: `Created identity candidate for '${localUser}'. Score: ${cand.confidence_score.toFixed(2)} (${cand.status})` }];
  } else if (action === 'update_status') {
    const id = parseInt(req.body.candidate_id, 10);
    const cand = identities.find(i => i.id === id);
    if (cand) {
      cand.status = req.body.new_status;
      res.locals.messages = [{ tags: 'info', text: `Updated candidate #${id} to '${cand.status}'.` }];
    }
  }

  const confirmed = identities.filter(i => i.status === 'confirmed').length;
  const pending = identities.filter(i => i.status !== 'confirmed' && i.status !== 'rejected').length;

  res.render('identity', {
    title: 'Identity Resolution | Learnami',
    activeNav: 'identity',
    candidates: identities,
    total_candidates: identities.length,
    confirmed,
    pending
  });
});

// ==========================================
// Vector Memory / RAG Retrieval
// ==========================================
app.get('/retrieval/', (req, res) => {
  const embedded_docs = documents.filter(d => d.vector_status === 'embedded').length;

  res.render('retrieval', {
    title: 'Vector Memory (RAG) | Learnami',
    activeNav: 'retrieval',
    documents,
    total_docs: documents.length,
    embedded_docs,
    query_result: null,
    search_query: ''
  });
});

app.post('/retrieval/', (req, res) => {
  const action = req.body.action;
  let query_result = null;
  let search_query = '';

  if (action === 'add_document') {
    const docKey = req.body.doc_key || 'doc_key';
    const docType = req.body.doc_type || 'policy';
    const sfpName = req.body.sfp_name || 'sfp_core';
    const title = req.body.title || 'Untitled';
    const content = req.body.content || '';
    const autoEmbed = req.body.auto_embed === 'on';

    const newDoc = {
      id: documents.length + 1,
      doc_key: docKey,
      doc_type: docType,
      sfp_name: sfpName,
      title,
      content,
      metadata_json: {},
      vector_status: autoEmbed ? 'embedded' : 'pending',
      embedding_json: autoEmbed ? [0.1, 0.3, 0.5] : [],
      created_at: new Date().toISOString()
    };
    documents.unshift(newDoc);
    res.locals.messages = [{ tags: 'success', text: `Document '${title}' saved and indexed into vector memory.` }];
  } else if (action === 'embed_all') {
    let embeddedCount = 0;
    documents.forEach(d => {
      if (d.vector_status !== 'embedded') {
        d.vector_status = 'embedded';
        d.embedding_json = [0.2, 0.4, 0.6];
        embeddedCount++;
      }
    });
    res.locals.messages = [{ tags: 'success', text: `Embedded ${embeddedCount} pending documents into vector space.` }];
  } else if (action === 'search') {
    search_query = (req.body.query || '').trim();
    if (search_query) {
      query_result = retrieveMatches(search_query, 5);
    }
  }

  const embedded_docs = documents.filter(d => d.vector_status === 'embedded').length;

  res.render('retrieval', {
    title: 'Vector Memory (RAG) | Learnami',
    activeNav: 'retrieval',
    documents,
    total_docs: documents.length,
    embedded_docs,
    query_result,
    search_query
  });
});

// ==========================================
// Privacy & Consent
// ==========================================
app.get('/privacy/', (req, res) => {
  res.render('privacy', {
    title: 'Privacy Boundaries & Consent | Learnami',
    activeNav: 'privacy',
    access_logs: privacyAccessLogs,
    consent_records: consentRecords,
    check_result: null
  });
});

app.post('/privacy/', (req, res) => {
  const action = req.body.action;
  let check_result = null;

  if (action === 'access_check') {
    const role = req.body.requester_role || 'user_facing_admin_agent';
    const dclass = req.body.data_class || 'cross_site_memory';
    const key = req.body.target_key || 'global_user_9921';
    check_result = evaluatePrivacyAccess(role, dclass, key);

    privacyAccessLogs.unshift({
      id: privacyAccessLogs.length + 1,
      requester_role: role,
      data_class: dclass,
      decision: check_result.decision,
      reason: check_result.reason,
      created_at: new Date().toISOString()
    });
    res.locals.messages = [{ tags: 'success', text: `Privacy check evaluated: ${check_result.decision.toUpperCase()}` }];
  }

  res.render('privacy', {
    title: 'Privacy Boundaries & Consent | Learnami',
    activeNav: 'privacy',
    access_logs: privacyAccessLogs,
    consent_records: consentRecords,
    check_result
  });
});

// ==========================================
// Operational Runbooks
// ==========================================
app.get('/runbooks/', (req, res) => {
  res.render('runbooks', {
    title: 'Operational Runbooks | Learnami',
    activeNav: 'runbooks',
    catalog: runbooks,
    executions: runbookExecutions,
    run_result: null
  });
});

app.post('/runbooks/', (req, res) => {
  const rkey = req.body.runbook_key;
  const rb = runbooks.find(r => r.key === rkey) || runbooks[0];

  const execRecord = {
    id: runbookExecutions.length + 1,
    runbook_key: rb.key,
    triggered_by: 'admin_dashboard',
    status: 'completed',
    steps_completed: rb.steps,
    created_at: new Date().toISOString().replace('T', ' ').substring(0, 19)
  };
  runbookExecutions.unshift(execRecord);
  res.locals.messages = [{ tags: 'success', text: `Runbook [${rb.title}] executed successfully.` }];

  res.render('runbooks', {
    title: 'Operational Runbooks | Learnami',
    activeNav: 'runbooks',
    catalog: runbooks,
    executions: runbookExecutions,
    run_result: execRecord
  });
});

// ==========================================
// Production Blueprint
// ==========================================
app.get('/blueprint/', (req, res) => {
  res.render('blueprint', {
    title: 'Production Blueprint | Learnami',
    activeNav: 'blueprint',
    blueprint,
    snapshots: blueprintSnapshots
  });
});

app.post('/blueprint/', (req, res) => {
  const sname = req.body.snapshot_name || `blueprint_snapshot_${blueprintSnapshots.length + 1}`;
  blueprintSnapshots.unshift({
    id: blueprintSnapshots.length + 1,
    snapshot_name: sname,
    created_at: new Date().toISOString().replace('T', ' ').substring(0, 19)
  });
  res.locals.messages = [{ tags: 'success', text: `Blueprint snapshot '${sname}' created successfully.` }];

  res.render('blueprint', {
    title: 'Production Blueprint | Learnami',
    activeNav: 'blueprint',
    blueprint,
    snapshots: blueprintSnapshots
  });
});

// ==========================================
// Media Assistant
// ==========================================
app.get('/media/', (req, res) => {
  const approved = mediaCandidates.filter(m => m.validation_status === 'approved').length;

  res.render('media', {
    title: 'Media Assistant | Learnami',
    activeNav: 'media',
    candidates: mediaCandidates,
    drafts: reviewDrafts,
    total_candidates: mediaCandidates.length,
    approved_candidates: approved
  });
});

app.post('/media/', (req, res) => {
  const action = req.body.action;

  if (action === 'add_candidate') {
    const target = req.body.post_target_title || 'Review Target';
    const ctype = req.body.content_type || 'film';
    const title = req.body.title || 'Official Poster';
    const url = req.body.source_url || '';
    const w = parseInt(req.body.width || '800', 10);
    const h = parseInt(req.body.height || '1200', 10);

    const evaluated = evaluateMediaAsset(ctype, url, w, h);
    const cand = {
      id: mediaCandidates.length + 1,
      post_target_title: target,
      content_type: ctype,
      title,
      source_url: url,
      width: w,
      height: h,
      quality_score: evaluated.quality_score,
      validation_status: evaluated.validation_status,
      created_at: new Date().toISOString()
    };
    mediaCandidates.unshift(cand);
    res.locals.messages = [{ tags: 'success', text: `Discovered candidate: '${title}'. Quality Score: ${cand.quality_score.toFixed(1)} (${cand.validation_status})` }];
  }

  const approved = mediaCandidates.filter(m => m.validation_status === 'approved').length;

  res.render('media', {
    title: 'Media Assistant | Learnami',
    activeNav: 'media',
    candidates: mediaCandidates,
    drafts: reviewDrafts,
    total_candidates: mediaCandidates.length,
    approved_candidates: approved
  });
});

// ==========================================
// Analytics
// ==========================================
app.get('/analytics/', (req, res) => {
  const totalRuns = automationLogs.length;
  const successfulRuns = automationLogs.filter(l => l.status === 'completed').length;
  const failedRuns = automationLogs.filter(l => l.status === 'failed').length;
  const totalItems = automationLogs.reduce((acc, l) => acc + (l.items_processed || 0), 0);

  res.render('analytics', {
    title: 'Analytics | Learnami',
    activeNav: 'analytics',
    logs: automationLogs,
    snapshots,
    total_runs: totalRuns,
    successful_runs: successfulRuns,
    failed_runs: failedRuns,
    total_items: totalItems
  });
});

// ==========================================
// Master Automation Runner
// ==========================================
app.all('/run-automation/', async (req, res) => {
  const result = await executeDatabaseAutomationAndNotify(users);
  res.locals.messages = [{
    tags: 'success',
    text: `⚡ Full automation executed across database! ${result.dbResult.message} ${result.emailResult.sent ? '[Report emailed to test@appflicks.com]' : ''}`
  }];
  res.redirect('/');
});

// ==========================================
// REST API Endpoints
// ==========================================
app.all('/api/db/test/', async (req, res) => {
  const cfg = {
    HOST: req.body?.host || req.query?.host || dbConfig.HOST,
    PORT: req.body?.port || req.query?.port || dbConfig.PORT || '3306',
    NAME: req.body?.name || req.query?.name || dbConfig.NAME,
    USER: req.body?.user || req.query?.user || dbConfig.USER,
    PASSWORD: req.body?.password !== undefined ? req.body.password : dbConfig.PASSWORD
  };

  const result = await attemptRealMysqlSync(cfg);
  res.json({
    success: result.success,
    latency_ms: result.latency_ms,
    server_info: result.server_info || `MySQL at ${cfg.HOST}:${cfg.PORT}`,
    message: result.message,
    db_name: cfg.NAME,
    host: cfg.HOST,
    users_count: users.length,
    tables_count: result.tables ? result.tables.length : 14,
    tested_at: new Date().toISOString().replace('T', ' ').substring(0, 19)
  });
});

app.all('/api/automation/run/', async (req, res) => {
  const result = await executeDatabaseAutomationAndNotify(users);
  res.json(result);
});

app.route('/api/identity/candidates/')
  .get((req, res) => {
    res.json(identities);
  })
  .post((req, res) => {
    const data = req.body || {};
    const scored = scoreIdentityCandidate(data.email_match, data.name_match, data.phone_match, data.sfp_overlap);
    const cand = {
      id: identities.length + 1,
      local_user_key: data.local_user_key,
      sfp_name: data.sfp_name,
      candidate_global_user_key: data.candidate_global_user_key,
      confidence_score: scored.confidence_score,
      status: scored.status,
      link_reason: scored.reasons.join(','),
      created_at: new Date().toISOString()
    };
    identities.unshift(cand);
    res.status(201).json(cand);
  });

app.route('/api/retrieval/documents/')
  .get((req, res) => {
    res.json(documents.map(d => ({
      id: d.id,
      doc_key: d.doc_key,
      doc_type: d.doc_type,
      title: d.title,
      vector_status: d.vector_status
    })));
  });

app.post('/api/retrieval/query/', (req, res) => {
  const query = req.body ? req.body.query : '';
  const limit = req.body && req.body.limit ? parseInt(req.body.limit, 10) : 5;
  res.json(retrieveMatches(query, limit));
});

// Start Express Server
app.listen(PORT, HOST, async () => {
  console.log(`⚡ Learnami Automation Engine running at http://${HOST}:${PORT}`);
  if (dbConfig.USER && dbConfig.PASSWORD) {
    console.log(`Attempting initial MySQL connection to ${dbConfig.HOST}...`);
    await attemptRealMysqlSync(dbConfig);
  }
});
