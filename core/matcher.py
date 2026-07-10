def normalize(value: str) -> str:
    return value.lower().strip()


def flatten_skills(profile: dict) -> list[str]:
    skills = []

    # Main skill categories
    for category_skills in profile.get("skills", {}).values():
        skills.extend(category_skills)

    # Experience bullet skills
    for exp in profile.get("experience", []):
        for bullet in exp.get("bullets", []):
            skills.extend(bullet.get("skills", []))

    # Project bullet skills
    for project in profile.get("projects", []):
        for bullet in project.get("bullets", []):
            skills.extend(bullet.get("skills", []))

    return sorted(set(skills))


def match_skills(job_keywords: list[str], profile: dict) -> dict:
    profile_skills = flatten_skills(profile)

    normalized_profile_skills = {
        normalize(skill): skill
        for skill in profile_skills
    }

    matched = []
    missing = []

    for keyword in job_keywords:
        normalized_keyword = normalize(keyword)

        if normalized_keyword in normalized_profile_skills:
            matched.append(normalized_profile_skills[normalized_keyword])
        else:
            missing.append(keyword)

    return {
        "matched": sorted(set(matched)),
        "missing": sorted(set(missing)),
        "profile_skills": profile_skills,
    }


def collect_all_bullets(profile: dict) -> list[dict]:
    bullets = []

    for exp in profile.get("experience", []):
        for bullet in exp.get("bullets", []):
            bullets.append({
                "section": "experience",
                "parent": exp.get("company"),
                "title": exp.get("title"),
                **bullet,
            })

    for project in profile.get("projects", []):
        for bullet in project.get("bullets", []):
            bullets.append({
                "section": "projects",
                "parent": project.get("name"),
                "title": project.get("name"),
                **bullet,
            })

    return bullets


def score_bullet_against_job(
    bullet: dict,
    job_keywords: list[str],
    role_keywords: list[str] | None = None
) -> int:
    bullet_skills = [
        normalize(skill)
        for skill in bullet.get("skills", [])
    ]

    normalized_job_keywords = [
        normalize(keyword)
        for keyword in job_keywords
    ]

    normalized_role_keywords = [
        normalize(keyword)
        for keyword in (role_keywords or [])
    ]

    score = 0

    # Job description keywords are the strongest signal.
    for keyword in normalized_job_keywords:
        if keyword in bullet_skills:
            score += 3
        elif any(keyword in skill or skill in keyword for skill in bullet_skills):
            score += 1

    # Role profile keywords are a secondary boost.
    for keyword in normalized_role_keywords:
        if keyword in bullet_skills:
            score += 2
        elif any(keyword in skill or skill in keyword for skill in bullet_skills):
            score += 1

    return score


def recommend_bullets(
    profile: dict,
    job_keywords: list[str],
    role_keywords: list[str] | None = None,
    limit: int = 10
) -> list[dict]:
    bullets = collect_all_bullets(profile)

    scored = []
    for bullet in bullets:
        score = score_bullet_against_job(
            bullet=bullet,
            job_keywords=job_keywords,
            role_keywords=role_keywords
        )

        if score > 0:
            scored.append({
                **bullet,
                "score": score,
            })

    scored.sort(key=lambda item: item["score"], reverse=True)

    return scored[:limit]

def calculate_match_score(matched: list[str], missing: list[str]) -> int:
    total = len(matched) + len(missing)

    if total == 0:
        return 0

    return round((len(matched) / total) * 100)