
import os
import json
import streamlit as st
from google import genai

# Configuration
MODEL = "gemini-3.8-flash"

st.set_page_config(
    page_title="AI Job Agent",
    page_icon="💼",
    layout="wide",
)

st.title("💼 AI Job Agent")
st.write(
    "Analyze job advertisements, evaluate your fit, "
    "and generate tailored cover letters."
)

# Load API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error(
        "Gemini API key not found. Set GEMINI_API_KEY "
        "in your VS Code terminal and restart the app."
    )
    st.stop()

client = genai.Client(api_key=api_key)


def generate_json(prompt):
    """Ask Gemini for a JSON response and parse it."""
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
    )

    text = response.text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "", 1)
        text = text.rsplit("```", 1)[0].strip()

    return json.loads(text)


def load_profile():
    """Load the candidate profile from profile.json."""
    with open("profile.json", encoding="utf-8") as file:
        return json.load(file)


def analyze_job(description):
    return generate_json(f"""
Extract the following information from this job advertisement.

JOB ADVERTISEMENT:
{description}

Return only valid JSON with exactly these keys:
{{
  "job_title": "",
  "company": "",
  "location": "",
  "type_of_position": "",
  "employment_type": "",
  "remote": "true, false, or unknown",
  "requirements": [],
  "skills": []
}}

Use "unknown" if remote status cannot be determined.
Do not invent information.
""")


def match_job(job, profile):
    return generate_json(f"""
You are an honest job-matching assistant.

JOB:
{json.dumps(job, ensure_ascii=False)}

CANDIDATE PROFILE:
{json.dumps(profile, ensure_ascii=False)}

Evaluate:
- Match percentage from 0 to 100
- Strong matches
- Missing or weak requirements
- Relevant experience
- Concerns or gaps
- Whether the candidate should apply
- Whether the location is suitable

The candidate lives in Chemnitz, Germany.
Fully remote jobs in Germany are location-suitable.
For on-site or hybrid jobs, consider commuting within
approximately 1.5 hours by public transport.
If uncertain, use "unknown" rather than guessing.

Be honest. Never invent qualifications or experience.

Return only valid JSON with exactly these keys:
{{
  "match_percentage": 0,
  "strong_matches": [],
  "missing_or_weak_requirements": [],
  "relevant_experience": [],
  "concerns_or_gaps": [],
  "recommendation": "",
  "remote": "true, false, or unknown",
  "commute_suitable": "true, false, or unknown",
  "location_reason": ""
}}
""")


def generate_cover_letter(job, profile):
    return generate_json(f"""
Write a tailored, professional cover letter for this job.

JOB:
{json.dumps(job, ensure_ascii=False)}

CANDIDATE PROFILE:
{json.dumps(profile, ensure_ascii=False)}

Use only the candidate's actual qualifications and experience.
Do not invent information.
Return only valid JSON with exactly this key:
{{"cover_letter": ""}}
""")


# User interface
job_text = st.text_area(
    "Paste the job advertisement",
    height=280,
    placeholder=(
        "Paste the complete job description here, "
        "including the requirements and location..."
    ),
)

analyze_button = st.button(
    "🔍 Analyze job",
    type="primary",
    disabled=not job_text.strip(),
)

if analyze_button:
    try:
        with st.spinner("Analyzing the job advertisement..."):
            profile = load_profile()
            job = analyze_job(job_text)
            recommendation = match_job(job, profile)

        st.session_state["job"] = job
        st.session_state["recommendation"] = recommendation
        st.session_state["profile"] = profile
        st.session_state.pop("cover_letter", None)

    except Exception as error:
        st.error(f"Analysis failed: {error}")

# Display results
if "job" in st.session_state:
    job = st.session_state["job"]
    recommendation = st.session_state["recommendation"]

    st.divider()
    st.header(job.get("job_title", "Job analysis"))

    col1, col2, col3 = st.columns(3)

    col1.metric("Company", job.get("company") or "Unknown")
    col2.metric("Location", job.get("location") or "Unknown")
    col3.metric(
        "Match score",
        f"{recommendation.get('match_percentage', 0)}%",
    )

    with st.expander("📋 Job details", expanded=True):
        st.write("**Position:**", job.get("type_of_position"))
        st.write("**Employment type:**", job.get("employment_type"))
        st.write("**Remote:**", job.get("remote"))
        st.write("**Required skills:**")
        st.write(job.get("skills", []))
        st.write("**Requirements:**")
        st.write(job.get("requirements", []))

    st.subheader("🎯 Your match")

    st.write("**Recommendation:**")
    st.write(recommendation.get("recommendation", ""))

    st.write("**Your strengths**")
    st.write(recommendation.get("strong_matches", []))

    st.write("**Missing or weak requirements**")
    st.write(recommendation.get("missing_or_weak_requirements", []))

    st.write("**Relevant experience**")
    st.write(recommendation.get("relevant_experience", []))

    st.write("**Concerns or gaps**")
    st.write(recommendation.get("concerns_or_gaps", []))

    st.write("**Location assessment**")
    st.write(recommendation.get("location_reason", ""))

    commute = recommendation.get("commute_suitable")

    if commute is True or str(commute).lower() == "true":
        st.success("Location marked as suitable.")

        if st.button("✍️ Generate cover letter"):
            try:
                with st.spinner("Writing your cover letter..."):
                    result = generate_cover_letter(
                        job,
                        st.session_state["profile"],
                    )
                    st.session_state["cover_letter"] = (
                        result["cover_letter"]
                    )
            except Exception as error:
                st.error(f"Cover letter generation failed: {error}")

    elif commute is False or str(commute).lower() == "false":
        st.warning(
            "This job was marked as unsuitable based on location. "
            "Review the location assessment before deciding."
        )
    else:
        st.info(
            "Location suitability is uncertain. "
            "Review the location assessment before deciding."
        )

    if "cover_letter" in st.session_state:
        st.subheader("✉️ Your cover letter")
        st.text_area(
            "Review and edit your cover letter",
            value=st.session_state["cover_letter"],
            height=350,
        )
        st.download_button(
            "Download cover letter",
            data=st.session_state["cover_letter"],
            file_name="cover_letter.txt",
            mime="text/plain",
        )
