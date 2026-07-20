from collections import defaultdict

from core.matcher import collect_all_bullets, score_bullet_against_job


EXPERIENCE_MIN_BULLETS = 5
EXPERIENCE_MAX_BULLETS = 6

BALANCED_TOTAL_TARGET = 19
BALANCED_TOTAL_MAX = 20

COMPACT_TOTAL_TARGET = 13
COMPACT_TOTAL_MAX = 14

MIN_PROJECT_BULLETS = 3
PREFERRED_PROJECT_BULLETS = 4


BULLET_TYPE_WEIGHTS = {
    "anchor": 5,
    "matched": 4,
    "technical_depth": 3,
    "product_thinking": 3,
    "support": 2,
}


PROJECT_ROLE_WEIGHTS = {
    "flagship": 6,
    "supporting": 2,
}


def _bullet_key(bullet: dict) -> str:
    return bullet.get("text", "").strip().lower()


def _dedupe_bullets(bullets: list[dict]) -> list[dict]:
    seen = set()
    unique = []

    for bullet in bullets:
        key = _bullet_key(bullet)

        if key and key not in seen:
            unique.append(bullet)
            seen.add(key)

    return unique


def _score_bullet(
    bullet: dict,
    job_keywords: list[str],
    role_keywords: list[str],
    selected_keys: set[str],
) -> dict:
    base_score = score_bullet_against_job(
        bullet=bullet,
        job_keywords=job_keywords,
        role_keywords=role_keywords,
    )

    bullet_type = bullet.get("bullet_type", "support")
    type_score = BULLET_TYPE_WEIGHTS.get(bullet_type, 1)

    selected_boost = 4 if _bullet_key(bullet) in selected_keys else 0

    return {
        **bullet,
        "score": bullet.get("score", 0) + base_score + type_score + selected_boost,
    }


def _get_project_role(profile: dict, project_name: str) -> str:
    for project in profile.get("projects", []):
        if project.get("name") == project_name:
            return project.get("project_role", "supporting")

    return "supporting"


def _rank_bullets(
    bullets: list[dict],
    job_keywords: list[str],
    role_keywords: list[str],
    selected_keys: set[str],
) -> list[dict]:
    scored = [
        _score_bullet(
            bullet=bullet,
            job_keywords=job_keywords,
            role_keywords=role_keywords,
            selected_keys=selected_keys,
        )
        for bullet in bullets
    ]

    scored.sort(key=lambda item: item.get("score", 0), reverse=True)
    return scored


def _take_unique(
    final_bullets: list[dict],
    candidates: list[dict],
    limit: int,
) -> list[dict]:
    final_keys = {_bullet_key(bullet) for bullet in final_bullets}

    for candidate in candidates:
        if len(final_bullets) >= limit:
            break

        key = _bullet_key(candidate)

        if key and key not in final_keys:
            final_bullets.append(candidate)
            final_keys.add(key)

    return final_bullets


def _compose_experience(
    all_bullets: list[dict],
    selected_bullets: list[dict],
    job_keywords: list[str],
    role_keywords: list[str],
) -> tuple[list[dict], list[str]]:
    warnings = []

    selected_keys = {_bullet_key(bullet) for bullet in selected_bullets}

    all_experience = [
        bullet for bullet in all_bullets
        if bullet.get("section") == "experience"
    ]

    selected_experience = [
        bullet for bullet in selected_bullets
        if bullet.get("section") == "experience"
    ]

    ranked_experience = _rank_bullets(
        bullets=all_experience,
        job_keywords=job_keywords,
        role_keywords=role_keywords,
        selected_keys=selected_keys,
    )

    final_experience = _dedupe_bullets(selected_experience)

    final_experience = _take_unique(
        final_bullets=final_experience,
        candidates=ranked_experience,
        limit=EXPERIENCE_MAX_BULLETS,
    )

    if len(final_experience) < EXPERIENCE_MIN_BULLETS:
        warnings.append(
            f"Experience section has only {len(final_experience)} strong bullets. "
            f"Target is at least {EXPERIENCE_MIN_BULLETS}; add real evidence instead of filler."
        )

    return final_experience[:EXPERIENCE_MAX_BULLETS], warnings


def _group_project_bullets(bullets: list[dict]) -> dict[str, list[dict]]:
    grouped = defaultdict(list)

    for bullet in bullets:
        if bullet.get("section") == "projects":
            grouped[bullet.get("parent")].append(bullet)

    return dict(grouped)


def _score_projects(
    profile: dict,
    project_groups: dict[str, list[dict]],
) -> list[tuple[str, int]]:
    project_scores = []

    for project_name, bullets in project_groups.items():
        bullet_score = sum(
            bullet.get("score", 0)
            for bullet in sorted(
                bullets,
                key=lambda item: item.get("score", 0),
                reverse=True,
            )[:4]
        )

        project_role = _get_project_role(profile, project_name)
        role_score = PROJECT_ROLE_WEIGHTS.get(project_role, 0)

        project_scores.append((project_name, bullet_score + role_score))

    project_scores.sort(key=lambda item: item[1], reverse=True)
    return project_scores


def _compose_projects(
    profile: dict,
    all_bullets: list[dict],
    selected_bullets: list[dict],
    job_keywords: list[str],
    role_keywords: list[str],
    project_budget: int,
    compact: bool = False,
) -> tuple[list[dict], list[str]]:
    warnings = []

    selected_keys = {_bullet_key(bullet) for bullet in selected_bullets}

    all_project_bullets = [
        bullet for bullet in all_bullets
        if bullet.get("section") == "projects"
    ]

    ranked_project_bullets = _rank_bullets(
        bullets=all_project_bullets,
        job_keywords=job_keywords,
        role_keywords=role_keywords,
        selected_keys=selected_keys,
    )

    project_groups = _group_project_bullets(ranked_project_bullets)
    project_scores = _score_projects(profile, project_groups)

    final_projects = []

    if compact:
        project_targets = [4, 3, 3]
    else:
        project_targets = [5, 5, 4, 3]

    for index, (project_name, _) in enumerate(project_scores):
        if index >= len(project_targets):
            break

        remaining_budget = project_budget - len(final_projects)

        # Never add a project if it can only receive 1 bullet.
        if remaining_budget < MIN_PROJECT_BULLETS:
            break

        target_count = min(project_targets[index], remaining_budget)

        # If target drops below minimum, skip project entirely.
        if target_count < MIN_PROJECT_BULLETS:
            continue

        candidates = project_groups.get(project_name, [])

        before_count = len(final_projects)

        final_projects = _take_unique(
            final_bullets=final_projects,
            candidates=candidates,
            limit=len(final_projects) + target_count,
        )

        added_count = len(final_projects) - before_count

        # If project could not reach minimum, remove its orphan bullets.
        if added_count < MIN_PROJECT_BULLETS:
            final_projects = final_projects[:before_count]
            warnings.append(
                f"{project_name} was skipped because it had fewer than "
                f"{MIN_PROJECT_BULLETS} strong available bullets for this resume."
            )
            continue

        if added_count < PREFERRED_PROJECT_BULLETS:
            warnings.append(
                f"{project_name} was included with {added_count} bullets. "
                f"Consider adding more strong project evidence later."
            )

    return final_projects, warnings

def compose_resume_bullets(
    profile: dict,
    selected_bullets: list[dict],
    resume_mode: str,
    job_keywords: list[str],
    role_keywords: list[str],
) -> dict:
    """
    Evidence-first resume composition.

    Philosophy:
    - Experience is protected because it is real-world evidence.
    - Job fit influences emphasis, but does not destroy the candidate's core story.
    - Final resume should include both matched evidence and general candidate value.
    """

    if resume_mode == "Strict":
        return {
            "final_bullets": selected_bullets,
            "warnings": [],
            "notes": ["Strict mode used: only manually selected bullets included."],
        }

    all_bullets = collect_all_bullets(profile)

    experience_bullets, experience_warnings = _compose_experience(
        all_bullets=all_bullets,
        selected_bullets=selected_bullets,
        job_keywords=job_keywords,
        role_keywords=role_keywords,
    )

    if resume_mode == "Compact":
        total_target = COMPACT_TOTAL_TARGET
        total_max = COMPACT_TOTAL_MAX
        compact = True
    else:
        total_target = BALANCED_TOTAL_TARGET
        total_max = BALANCED_TOTAL_MAX
        compact = False

    project_budget = max(0, total_target - len(experience_bullets))

    project_bullets, project_warnings = _compose_projects(
        profile=profile,
        all_bullets=all_bullets,
        selected_bullets=selected_bullets,
        job_keywords=job_keywords,
        role_keywords=role_keywords,
        project_budget=project_budget,
        compact=compact,
    )

    final_bullets = _dedupe_bullets(experience_bullets + project_bullets)
    final_bullets = final_bullets[:total_max]

    notes = [
        f"Experience protected with target minimum of {EXPERIENCE_MIN_BULLETS} bullets.",
        "Final resume balances job-fit bullets with core candidate value.",
    ]

    return {
        "final_bullets": final_bullets,
        "warnings": experience_warnings + project_warnings,
        "notes": notes,
    }