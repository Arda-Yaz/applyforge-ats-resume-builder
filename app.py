import streamlit as st

from core.profile_loader import load_profile
from core.job_parser import extract_keywords, top_terms
from core.matcher import match_skills, recommend_bullets, calculate_match_score
from core.honesty_guard import filter_allowed_bullets
from core.cv_generator import generate_markdown_resume, save_markdown_resume, enhance_selected_bullets

st.set_page_config(
    page_title="ApplyForge - ATS Resume Builder",
    page_icon="📄",
    layout="wide"
)

st.title("ApplyForge")
st.caption("ATS-Friendly Resume Builder with Evidence-Based CV Generation")

profile = load_profile()

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

with st.sidebar:
    st.header("Candidate Profile")
    st.write(profile["personal"]["name"])
    st.write(profile["personal"]["location"])

    resume_mode = st.selectbox(
    "Resume Generation Mode",
    ["Strict", "Balanced", "Compact"],
    index=1
    )
    
    target_title = st.selectbox(
        "Target Title",
        profile.get("target_titles", ["Junior AI/ML/Data Engineer"])
    )

    st.divider()
    st.write("Core Skills")
    for category, skills in profile.get("skills", {}).items():
        st.caption(category)
        st.write(", ".join(skills))


st.header("1. Paste Job Description")

job_description = st.text_area(
    "Paste the job posting here:",
    height=300,
    placeholder="Paste the job description..."
)

if st.button("Analyze Job Description"):
    if not job_description.strip():
        st.warning("Please paste a job description first.")
        st.stop()

    job_keywords = extract_keywords(job_description)
    common_terms = top_terms(job_description)

    skill_match = match_skills(job_keywords, profile)
    recommended = recommend_bullets(profile, job_keywords, limit=10)

    allowed_bullets, blocked_bullets = filter_allowed_bullets(
        recommended,
        profile.get("blocked_claims", [])
    )

    score = calculate_match_score(
        skill_match["matched"],
        skill_match["missing"]
    )

    st.session_state.analysis_result = {
        "job_keywords": job_keywords,
        "common_terms": common_terms,
        "skill_match": skill_match,
        "allowed_bullets": allowed_bullets,
        "blocked_bullets": blocked_bullets,
        "score": score
    }

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
            key=f"bullet_select_{index}"
        )

        st.caption(
            f"Section: {bullet.get('section')} | Source: {bullet.get('parent')} | Evidence: {bullet.get('evidence', 'N/A')}"
        )

        if selected:
            selected_bullets.append(bullet)

    st.divider()

    if not selected_bullets:
        st.warning("Select at least one bullet to generate a resume.")
    else:
        enhanced_bullets = enhance_selected_bullets(
            profile=profile,
            selected_bullets=selected_bullets,
            min_project_bullets=2,
            max_project_bullets=4,
            min_experience_bullets=3,
            max_experience_bullets=5
        )

        context_added = [
            bullet for bullet in enhanced_bullets
            if bullet.get("context_added")
        ]
        
        if context_added:
            st.info(f"{len(context_added)} context bullet added to keep resume sections complete.")

        resume_md = generate_markdown_resume(
            profile=profile,
            selected_bullets=enhanced_bullets,
            target_title=target_title
        )

        output_path = save_markdown_resume(resume_md)

        st.header("Generated ATS Resume Draft")
        st.code(resume_md, language="markdown")

        st.download_button(
            label="Download Markdown Resume",
            data=resume_md,
            file_name="generated_resume.md",
            mime="text/markdown"
        )

        st.success(f"Resume generated and saved to {output_path}.")