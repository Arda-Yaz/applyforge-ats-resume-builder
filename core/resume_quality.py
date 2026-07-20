def count_bullets(grouped_resume: dict) -> dict:
    experience_bullets = 0
    project_bullets = 0

    for exp in grouped_resume.get("experience", []):
        experience_bullets += len(exp.get("selected_bullets", []))

    for project in grouped_resume.get("projects", []):
        project_bullets += len(project.get("selected_bullets", []))

    return {
        "experience_bullets": experience_bullets,
        "project_bullets": project_bullets,
        "total_bullets": experience_bullets + project_bullets,
    }


def build_resume_quality_report(
    resume_md: str,
    grouped_resume: dict,
    target_title: str
) -> dict:
    word_count = len(resume_md.split())
    character_count = len(resume_md)

    bullet_counts = count_bullets(grouped_resume)

    warnings = []
    strengths = []

    # Length checks
    if word_count < 350:
        warnings.append("Resume may be too short for a technical new graduate profile.")
    elif word_count > 950:
        warnings.append("Resume may be too long for a one-page ATS resume.")
    else:
        strengths.append("Resume length looks suitable for a one-page technical resume.")

    # Bullet checks
    if bullet_counts["total_bullets"] < 5:
        warnings.append("Resume has too few bullet points to show enough evidence.")
    else:
        strengths.append("Resume includes enough evidence-based bullet points.")

    if bullet_counts["experience_bullets"] == 0:
        warnings.append("Experience section has no bullet points.")
    elif bullet_counts["experience_bullets"] < 3:
        warnings.append("Experience section may look underdeveloped.")
    else:
        strengths.append("Experience section has enough detail.")

    if bullet_counts["project_bullets"] == 0:
        warnings.append("Projects section is missing or has no bullet points.")
    elif bullet_counts["project_bullets"] < 2:
        warnings.append("Projects section may look weak with fewer than 2 bullet points.")
    else:
        strengths.append("Projects section has enough supporting detail.")

    # Target title check
    if target_title.lower() not in resume_md.lower():
        warnings.append("Target title does not appear in the resume text.")
    else:
        strengths.append("Target title appears in the resume.")

    # Contact/link checks
    expected_terms = ["github", "linkedin"]
    for term in expected_terms:
        if term not in resume_md.lower():
            warnings.append(f"{term.title()} link may be missing.")
        else:
            strengths.append(f"{term.title()} link is present.")

    # Basic score
    score = 100
    score -= len(warnings) * 8
    score = max(0, min(100, score))

    return {
        "quality_score": score,
        "word_count": word_count,
        "character_count": character_count,
        "bullet_counts": bullet_counts,
        "warnings": warnings,
        "strengths": strengths,
    }