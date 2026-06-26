def flatten_skills(profile: dict) -> list[str]:
    skills = []

    for category_skills in profile.get("skills", {}).values():
        skills.extend(category_skills)

    return sorted(set(skills))


def normalize(value: str) -> str:
    return value.lower().strip()


def match_skills(job_keywords: list[str], profile: dict) -> dict:
    profile_skills = flatten_skills(profile)

    normalized_profile_skills = {normalize(skill): skill for skill in profile_skills}
    normalized_job_keywords = [normalize(keyword) for keyword in job_keywords]

    matched = []
    missing = []

    for keyword in normalized_job_keywords:
        if keyword in normalized_profile_skills:
            matched.append(normalized_profile_skills[keyword])
        else:
            missing.append(keyword)

    return {
        "matched": sorted(set(matched)),
        "missing": sorted(set(missing)),
        "profile_skills": profile_skills
    }


def collect_all_bullets(profile: dict) -> list[dict]:
    bullets = []

    for exp in profile.get("experience", []):
        for bullet in exp.get("bullets", []):
            bullets.append({
                "section": "experience",
                "parent": exp.get("company"),
                "title": exp.get("title"),
                **bullet
            })

    for project in profile.get("projects", []):
        for bullet in project.get("bullets", []):
            bullets.append({
                "section": "projects",
                "parent": project.get("name"),
                "title": project.get("name"),
                **bullet
            })

    return bullets


def score_bullet_against_job(bullet: dict, job_keywords: list[str]) -> int:
    bullet_skills = [normalize(skill) for skill in bullet.get("skills", [])]
    normalized_keywords = [normalize(keyword) for keyword in job_keywords]

    score = 0

    for keyword in normalized_keywords:
        if keyword in bullet_skills:
            score += 3
        elif any(keyword in skill or skill in keyword for skill in bullet_skills):
            score += 1

    return score


def recommend_bullets(profile: dict, job_keywords: list[str], limit: int = 8) -> list[dict]:
    bullets = collect_all_bullets(profile)

    scored = []
    for bullet in bullets:
        score = score_bullet_against_job(bullet, job_keywords)
        if score > 0:
            scored.append({
                **bullet,
                "score": score
            })

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:limit]

def calculate_match_score(matched: list[str], missing: list[str]) -> int:
    total = len(matched) + len(missing)

    if total == 0:
        return 0

    return round((len(matched) / total) * 100)