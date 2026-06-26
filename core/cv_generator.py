from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def _bullet_key(bullet: dict) -> str:
    return bullet.get("text", "").strip().lower()


def _collect_profile_bullets(profile: dict) -> list[dict]:
    bullets = []

    for exp in profile.get("experience", []):
        for bullet in exp.get("bullets", []):
            bullets.append({
                "section": "experience",
                "parent": exp.get("company"),
                "title": exp.get("title"),
                "score": bullet.get("score", 0),
                **bullet
            })

    for project in profile.get("projects", []):
        for bullet in project.get("bullets", []):
            bullets.append({
                "section": "projects",
                "parent": project.get("name"),
                "title": project.get("name"),
                "score": bullet.get("score", 0),
                **bullet
            })

    return bullets


def enhance_selected_bullets(
    profile: dict,
    selected_bullets: list[dict],
    min_project_bullets: int = 2,
    max_project_bullets: int = 4,
    min_experience_bullets: int = 3,
    max_experience_bullets: int = 5
) -> list[dict]:
    """
    Adds context bullets so resume sections do not look unfinished.
    Selected bullets are always preserved.
    """

    all_profile_bullets = _collect_profile_bullets(profile)

    enhanced = list(selected_bullets)
    selected_keys = {_bullet_key(bullet) for bullet in enhanced}

    def add_context_bullets(section: str, parent: str, min_count: int, max_count: int):
        nonlocal enhanced, selected_keys

        current = [
            bullet for bullet in enhanced
            if bullet.get("section") == section and bullet.get("parent") == parent
        ]

        if len(current) == 0:
            return

        if len(current) >= min_count:
            return

        candidates = [
            bullet for bullet in all_profile_bullets
            if bullet.get("section") == section
            and bullet.get("parent") == parent
            and _bullet_key(bullet) not in selected_keys
        ]

        needed = min_count - len(current)
        available_slots = max_count - len(current)
        to_add_count = min(needed, available_slots)

        for bullet in candidates[:to_add_count]:
            bullet_copy = bullet.copy()
            bullet_copy["score"] = bullet_copy.get("score", 0)
            bullet_copy["context_added"] = True

            enhanced.append(bullet_copy)
            selected_keys.add(_bullet_key(bullet_copy))

    for exp in profile.get("experience", []):
        add_context_bullets(
            section="experience",
            parent=exp.get("company"),
            min_count=min_experience_bullets,
            max_count=max_experience_bullets
        )

    for project in profile.get("projects", []):
        add_context_bullets(
            section="projects",
            parent=project.get("name"),
            min_count=min_project_bullets,
            max_count=max_project_bullets
        )

    return enhanced

def group_selected_bullets(profile: dict, selected_bullets: list[dict]) -> dict:
    experience = []
    projects = []

    for exp in profile.get("experience", []):
        exp_copy = exp.copy()
        exp_copy["selected_bullets"] = [
            bullet for bullet in selected_bullets
            if bullet.get("section") == "experience" and bullet.get("parent") == exp.get("company")
        ]

        if exp_copy["selected_bullets"]:
            experience.append(exp_copy)

    for project in profile.get("projects", []):
        project_copy = project.copy()
        project_copy["selected_bullets"] = [
            bullet for bullet in selected_bullets
            if bullet.get("section") == "projects" and bullet.get("parent") == project.get("name")
        ]

        if project_copy["selected_bullets"]:
            projects.append(project_copy)

    return {
        "experience": experience,
        "projects": projects
    }


def generate_markdown_resume(
    profile: dict,
    selected_bullets: list[dict],
    target_title: str = "Junior AI/ML/Data Engineer",
    template_path: str = "templates/ats_resume_template.md"
) -> str:
    template_file = Path(template_path)

    env = Environment(
        loader=FileSystemLoader(str(template_file.parent)),
        autoescape=False
    )

    template = env.get_template(template_file.name)
    grouped = group_selected_bullets(profile, selected_bullets)

    rendered = template.render(
        personal=profile["personal"],
        target_title=target_title,
        summary=profile["summary"],
        skills=profile["skills"],
        experience=grouped["experience"],
        projects=grouped["projects"],
        education=profile["education"]
    )

    return rendered.strip()


def save_markdown_resume(content: str, output_path: str = "exports/generated_resume.md") -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return str(path)