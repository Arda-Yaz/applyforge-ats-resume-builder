import streamlit as st

st.set_page_config(
    page_title="ApplyForge - ATS Resume Builder",
    page_icon="📄",
    layout="wide"
)

st.title("ApplyForge")
st.subheader("ATS-Friendly Resume Builder")

job_description = st.text_area(
    "Paste the job description here:",
    height=300,
    placeholder="Paste job posting text..."
)

if st.button("Analyze Job"):
    if not job_description.strip():
        st.warning("Please paste a job description first.")
    else:
        st.success("Job description received. Analysis module will be added next.")
        st.write(job_description[:1000])