import streamlit as st

from core.resume_quality import build_resume_quality_report
from core.docx_exporter import export_resume_to_docx
from core.ats_preview import extract_docx_text, build_ats_preview_report
from core.profile_loader import load_profile
from core.job_parser import extract_keywords, top_terms
from core.matcher import match_skills, recommend_bullets, calculate_match_score
from core.honesty_guard import filter_allowed_bullets
from core.cv_generator import (
    generate_markdown_resume,
    group_selected_bullets,
    save_markdown_resume,
    enhance_selected_bullets,
    get_role_profile,
    reorder_skills_by_role,
)


st.set_page_config(
    page_title="ApplyForge - ATS Resume Builder",
    page_icon="📄",
    layout="wide",
)

st.title("ApplyForge")
st.caption("ATS-Friendly Resume Builder with Evidence-Based CV Generation")

profile = load_profile()

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "generate_resume_clicked" not in st.session_state:
    st.session_state.generate_resume_clicked = False


with st.sidebar:
    st.header("Candidate Profile")
    st.write(profile["personal"]["name"])
    st.write(profile["personal"]["location"])

    role_options = list(profile.get("role_profiles", {}).keys())

    selected_role = st.selectbox(
        "Role Profile",
        role_options if role_options else ["AI/ML Engineer"],
        index=0,
    )

    role_profile = get_role_profile(profile, selected_role)

    target_title = role_profile["target_title"]
    role_summary = role_profile["summary"]
    role_skills = reorder_skills_by_role(profile, role_profile)
    role_keywords = role_profile.get("preferred_keywords", [])

    st.caption(f"Target Title: {target_title}")

    resume_mode = st.selectbox(
        "Resume Generation Mode",
        ["Strict", "Balanced", "Compact"],
        index=1,
    )

    st.caption("Strict: only selected bullets")
    st.caption("Balanced: selected bullets + context bullets")
    st.caption("Compact: strongest selected bullets only")

    st.divider()

    generate_resume_button = st.button(
        "Generate Resume",
        use_container_width=True,
    )

    if generate_resume_button:
        st.session_state.generate_resume_clicked = True

    st.divider()

    st.write("Core Skills")
    for category, skills in role_skills.items():
        st.caption(category)
        st.write(", ".join(skills))


st.header("1. Paste Job Description")

job_description = st.text_area(
    "Paste the job posting here:",
    height=300,
    placeholder="Paste the job description...",
)


if st.button("Analyze Job Description"):
    if not job_description.strip():
        st.warning("Please paste a job description first.")
        st.stop()

    job_keywords = extract_keywords(job_description)
    common_terms = top_terms(job_description)

    combined_keywords = sorted(set(job_keywords + role_keywords))

    skill_match = match_skills(combined_keywords, profile)

    recommended = recommend_bullets(
        profile=profile,
        job_keywords=job_keywords,
        role_keywords=role_keywords,
        limit=10,
    )

    allowed_bullets, blocked_bullets = filter_allowed_bullets(
        recommended,
        profile.get("blocked_claims", []),
    )

    score = calculate_match_score(
        skill_match["matched"],
        skill_match["missing"],
    )

    st.session_state.analysis_result = {
        "job_keywords": job_keywords,
        "role_keywords": role_keywords,
        "combined_keywords": combined_keywords,
        "common_terms": common_terms,
        "skill_match": skill_match,
        "allowed_bullets": allowed_bullets,
        "blocked_bullets": blocked_bullets,
        "score": score,
    }

    st.session_state.generate_resume_clicked = False


if st.session_state.analysis_result:
    result = st.session_state.analysis_result

    st.metric("ATS Match Score", f"{result['score']}%")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Detected Job Keywords")
        if result["job_keywords"]:
            st.success(", ".join(result["job_keywords"]))
        else:
            st.info("No predefined keywords detected yet.")

        st.subheader("Role Keywords")
        if role_keywords:
            st.info(", ".join(role_keywords))
        else:
            st.info("No role keywords found.")

        st.subheader("Combined Matching Keywords")
        st.write(sorted(set(result["job_keywords"] + role_keywords)))

        st.subheader("Matched Skills")
        if result["skill_match"]["matched"]:
            st.write(result["skill_match"]["matched"])
        else:
            st.warning("No direct skill matches found.")

        st.subheader("Missing / Weak Skills")
        if result["skill_match"]["missing"]:
            st.write(result["skill_match"]["missing"])
        else:
            st.success("No missing skills detected from predefined keyword list.")

    with col2:
        st.subheader("Top Terms in Job Description")
        st.write(result["common_terms"])

        if result["blocked_bullets"]:
            st.subheader("Blocked Claims")
            for bullet in result["blocked_bullets"]:
                st.error(bullet["text"])
                st.caption(bullet["block_reason"])

    st.divider()

    st.header("Manual Bullet Selection")
    st.caption("Select the bullets you want to include in the tailored resume.")

    selected_bullets = []

    for index, bullet in enumerate(result["allowed_bullets"]):
        label = f"[Score: {bullet['score']}] {bullet['text']}"

        selected = st.checkbox(
            label,
            value=True,
            key=f"bullet_select_{index}",
        )

        st.caption(
            f"Section: {bullet.get('section')} | "
            f"Source: {bullet.get('parent')} | "
            f"Evidence: {bullet.get('evidence', 'N/A')}"
        )

        if selected:
            selected_bullets.append(bullet)

    st.divider()

    if not selected_bullets:
        st.warning("Select at least one bullet to generate a resume.")
        st.stop()

    st.info(
        "Use the Generate Resume button in the sidebar to create the Markdown and DOCX files."
    )

    if st.session_state.generate_resume_clicked:
        if resume_mode == "Strict":
            final_bullets = selected_bullets

        elif resume_mode == "Balanced":
            final_bullets = enhance_selected_bullets(
                profile=profile,
                selected_bullets=selected_bullets,
                min_project_bullets=2,
                max_project_bullets=4,
                min_experience_bullets=3,
                max_experience_bullets=5,
            )

            context_added = [
                bullet for bullet in final_bullets
                if bullet.get("context_added")
            ]

            if context_added:
                st.info(
                    f"{len(context_added)} context bullet added to keep resume sections complete."
                )

        elif resume_mode == "Compact":
            final_bullets = sorted(
                selected_bullets,
                key=lambda bullet: bullet.get("score", 0),
                reverse=True,
            )[:6]

        else:
            final_bullets = selected_bullets

        resume_md = generate_markdown_resume(
            profile=profile,
            selected_bullets=final_bullets,
            target_title=target_title,
            summary=role_summary,
            skills=role_skills,
        )

        markdown_output_path = save_markdown_resume(resume_md)

        grouped_resume = group_selected_bullets(
            profile=profile,
            selected_bullets=final_bullets,
        )

        resume_quality_report = build_resume_quality_report(
        resume_md=resume_md,
        grouped_resume=grouped_resume,
        target_title=target_title,
        )

        docx_output_path = export_resume_to_docx(
            profile=profile,
            grouped_resume=grouped_resume,
            target_title=target_title,
            summary=role_summary,
            skills=role_skills,
            output_path="exports/generated_resume.docx",
        )

        parsed_docx_text = extract_docx_text(docx_output_path)

        ats_preview_report = build_ats_preview_report(
            parsed_text=parsed_docx_text,
            job_keywords=sorted(set(result["job_keywords"] + role_keywords)),
        )

        st.header("Generated ATS Resume Draft")
        st.code(resume_md, language="markdown")

        st.divider()

        st.header("Resume Quality Guard")

        st.metric(
            "Resume Quality Score",
            f"{resume_quality_report['quality_score']}%"
        )

        quality_col1, quality_col2 = st.columns(2)

        with quality_col1:
            st.subheader("Resume Stats")
            st.write(f"Word count: {resume_quality_report['word_count']}")
            st.write(f"Character count: {resume_quality_report['character_count']}")

            bullet_counts = resume_quality_report["bullet_counts"]
            st.write(f"Experience bullets: {bullet_counts['experience_bullets']}")
            st.write(f"Project bullets: {bullet_counts['project_bullets']}")
            st.write(f"Total bullets: {bullet_counts['total_bullets']}")

        with quality_col2:
            st.subheader("Strengths")
            if resume_quality_report["strengths"]:
                for strength in resume_quality_report["strengths"]:
                    st.success(strength)
            else:
                st.info("No strengths detected yet.")

            st.subheader("Warnings")
            if resume_quality_report["warnings"]:
                for warning in resume_quality_report["warnings"]:
                    st.warning(warning)
            else:
                st.success("No major resume quality warnings detected.")

        st.download_button(
            label="Download Markdown Resume",
            data=resume_md,
            file_name="generated_resume.md",
            mime="text/markdown",
        )

        with open(docx_output_path, "rb") as file:
            st.download_button(
                label="Download DOCX Resume",
                data=file,
                file_name="generated_resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

        st.success(
            f"Resume generated. Markdown: {markdown_output_path} | DOCX: {docx_output_path}"
        )

        st.divider()

        st.header("ATS Text Preview")

        st.metric(
            "ATS Parse Health Score",
            f"{ats_preview_report['parse_score']}%",
        )

        preview_col1, preview_col2 = st.columns(2)

        with preview_col1:
            st.subheader("Detected Sections")

            for section, exists in ats_preview_report["section_status"].items():
                if exists:
                    st.success(f"{section}: detected")
                else:
                    st.error(f"{section}: missing")

        with preview_col2:
            st.subheader("Parse Diagnostics")

            st.write(f"Word count: {ats_preview_report['word_count']}")
            st.write(f"Character count: {ats_preview_report['character_count']}")

            if ats_preview_report["suspicious_characters"]:
                st.error(
                    "Suspicious characters detected: "
                    + ", ".join(ats_preview_report["suspicious_characters"])
                )
            else:
                st.success("No suspicious encoding characters detected.")

        st.subheader("Job Keywords Found in Generated Resume")

        keyword_status = ats_preview_report["keyword_status"]

        if keyword_status["matched"]:
            st.success(
                "Matched in generated resume: "
                + ", ".join(keyword_status["matched"])
            )
        else:
            st.warning("No job keywords found in generated resume.")

        if keyword_status["missing"]:
            st.warning(
                "Missing from generated resume: "
                + ", ".join(keyword_status["missing"])
            )
        else:
            st.success("All detected job keywords appear in the generated resume.")

        with st.expander("Show parsed ATS text"):
            st.text(ats_preview_report["parsed_text"])

else:
    st.info("Paste a job description and click Analyze Job Description to begin.")