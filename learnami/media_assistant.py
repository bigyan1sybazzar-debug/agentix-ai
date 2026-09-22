import uuid
import urllib.parse
from .models import MediaCandidate, MediaProvenanceLog, ReviewPostDraft

# Approved and trusted domain registry for governance
TRUSTED_DOMAINS = [
    "image.tmdb.org",
    "themoviedb.org",
    "images.igdb.com",
    "commons.wikimedia.org",
    "upload.wikimedia.org",
    "covers.openlibrary.org",
    "i.discogs.com",
    "media.steampowered.com",
    "m.media-amazon.com"
]

RESTRICTED_DOMAINS = [
    "pinterest.com",
    "shutterstock.com",
    "gettyimages.com"
]

TARGET_DIMENSIONS = {
    "film": {"min_w": 400, "min_h": 600, "target_ratio": 2/3, "ratio_name": "2:3"},
    "tv": {"min_w": 400, "min_h": 600, "target_ratio": 2/3, "ratio_name": "2:3"},
    "game": {"min_w": 500, "min_h": 650, "target_ratio": 3/4, "ratio_name": "3:4"},
    "album": {"min_w": 500, "min_h": 500, "target_ratio": 1/1, "ratio_name": "1:1"},
    "book": {"min_w": 400, "min_h": 600, "target_ratio": 2/3, "ratio_name": "2:3"},
    "thumbnail": {"min_w": 640, "min_h": 360, "target_ratio": 16/9, "ratio_name": "16:9"},
}


def extract_domain(url: str) -> str:
    """Safely extract netloc domain from URL."""
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc.lower() or "direct_upload"
    except Exception:
        return "unknown"


def evaluate_media_asset(content_type: str, source_url: str, width: int, height: int):
    """
    Workbook 13: 9-Step Governance & Validation Pipeline.
    Inspects dimensions, aspect ratio, domain trust, and computes a 0-100 quality score.
    """
    domain = extract_domain(source_url)
    target = TARGET_DIMENSIONS.get(content_type, TARGET_DIMENSIONS["film"])

    # 1. Domain Trust Score (max 30 pts)
    domain_score = 15.0
    rights_status = "editorial_caution"
    
    for trusted in TRUSTED_DOMAINS:
        if trusted in domain:
            domain_score = 30.0
            rights_status = "trusted"
            break

    for restricted in RESTRICTED_DOMAINS:
        if restricted in domain:
            domain_score = 5.0
            rights_status = "restricted"
            break

    # 2. Resolution Score (max 40 pts)
    min_w = target["min_w"]
    min_h = target["min_h"]
    res_score = 0.0
    if width >= min_w and height >= min_h:
        # Scale upwards to 40 based on resolution
        pixels = width * height
        ideal_pixels = (min_w * 1.5) * (min_h * 1.5)
        ratio = min(1.5, pixels / ideal_pixels)
        res_score = round(25.0 + (ratio * 10.0), 1)
        res_score = min(40.0, res_score)
    else:
        res_score = 10.0

    # 3. Aspect Ratio Score (max 30 pts)
    actual_ratio = (width / height) if height > 0 else 1.0
    diff = abs(actual_ratio - target["target_ratio"])
    if diff < 0.05:
        ratio_score = 30.0
    elif diff < 0.15:
        ratio_score = 20.0
    else:
        ratio_score = 10.0

    total_quality = round(domain_score + res_score + ratio_score, 1)

    # 4. Validation Status
    if rights_status == "restricted":
        validation_status = "rejected"
    elif total_quality >= 70.0 and res_score >= 20.0:
        validation_status = "approved"
    elif total_quality >= 45.0:
        validation_status = "review_required"
    else:
        validation_status = "rejected"

    return {
        "domain": domain,
        "aspect_ratio": target["ratio_name"],
        "quality_score": total_quality,
        "rights_status": rights_status,
        "validation_status": validation_status
    }


def register_media_candidate(post_target_title: str, content_type: str, title: str,
                             source_url: str, width: int = 800, height: int = 1200):
    """
    Registers a candidate image, evaluates it, and generates candidate ID.
    """
    eval_res = evaluate_media_asset(content_type, source_url, width, height)
    cand_id = f"cand_{uuid.uuid4().hex[:10]}"

    candidate = MediaCandidate.objects.create(
        post_target_title=post_target_title,
        content_type=content_type,
        candidate_id=cand_id,
        title=title,
        source_url=source_url,
        source_domain=eval_res["domain"],
        width=width,
        height=height,
        aspect_ratio=eval_res["aspect_ratio"],
        quality_score=eval_res["quality_score"],
        rights_status=eval_res["rights_status"],
        validation_status=eval_res["validation_status"]
    )
    return candidate


def package_review_post(draft_id: int, mode: str = "assisted"):
    """
    Workbook 13: Packages a review post with full WordPress Post-Meta schema
    compliant with learnami-agent-bridge plugin.
    """
    draft = ReviewPostDraft.objects.get(id=draft_id)
    package_id = f"pkg_{uuid.uuid4().hex[:8]}"

    meta_package = {
        "learnami_media_assistant_mode": mode,
        "learnami_agent_package_id": package_id,
        "learnami_assistance_applied": True,
        "learnami_autonomous_origin": (mode == "autonomous"),
        "post_title": draft.title,
        "content_type": draft.content_type,
    }

    if draft.selected_media:
        media = draft.selected_media
        meta_package.update({
            "learnami_media_candidate_id": media.candidate_id,
            "learnami_media_source_url": media.source_url,
            "learnami_media_source_domain": media.source_domain,
            "learnami_media_provenance_status": "verified" if media.validation_status == "approved" else "flagged",
            "learnami_media_review_required": (media.validation_status == "review_required"),
            "media_quality_score": media.quality_score,
            "media_dimensions": f"{media.width}x{media.height}"
        })

        # Create provenance log entry
        MediaProvenanceLog.objects.create(
            candidate=media,
            source_url=media.source_url,
            source_domain=media.source_domain,
            provenance_status="verified" if media.validation_status == "approved" else "flagged",
            review_required=(media.validation_status == "review_required"),
            assistance_applied=True,
            autonomous_origin=(mode == "autonomous"),
            agent_package_id=package_id,
            notes={"package_timestamp": str(package_id)}
        )

    draft.mode = mode
    draft.status = "packaged"
    draft.package_payload = meta_package
    draft.save()
    return draft


def run_automated_media_validation():
    """
    Self-automation runner for media candidates:
    Re-scores pending candidates and packages drafts ready for WordPress.
    """
    pending = MediaCandidate.objects.filter(validation_status="pending")
    revalidated = 0
    for cand in pending:
        res = evaluate_media_asset(cand.content_type, cand.source_url, cand.width, cand.height)
        cand.quality_score = res["quality_score"]
        cand.rights_status = res["rights_status"]
        cand.validation_status = res["validation_status"]
        cand.source_domain = res["domain"]
        cand.aspect_ratio = res["aspect_ratio"]
        cand.save()
        revalidated += 1

    # Auto-package pending drafts that have an approved candidate selected
    packaged_count = 0
    drafts = ReviewPostDraft.objects.filter(status="draft", selected_media__isnull=False)
    for d in drafts:
        if d.selected_media.validation_status == "approved":
            package_review_post(d.id, mode="autonomous")
            packaged_count += 1

    return {
        "revalidated_candidates": revalidated,
        "auto_packaged_drafts": packaged_count
    }
