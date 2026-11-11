
import os
import json
import re
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
import time
from google.genai import errors

# ============================================================
# 1. CONFIGURATION
# ============================================================

# Get the directory where main.py is located
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env
load_dotenv(BASE_DIR / ".env")

# Gemini API configuration
API_KEY = os.getenv("GEMINI_API_KEY")

# Use the model name from .env, or the default below.
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

# Candidate information
PROFILE_PATH = BASE_DIR / "profile-example.json"

# Location settings
CANDIDATE_LOCATION = "Chemnitz, Germany"
MAX_COMMUTE_HOURS = 1.5


# ============================================================
# 2. GEMINI CLIENT
# ============================================================

def get_gemini_client(api_key):

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing. "
            "Please check your .env file."
        )

    client = genai.Client(api_key=api_key)

    return client


# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

def parse_json_response(response):
    """
    Convert Gemini's response into a Python dictionary.
    """

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    clean_response = response.text.strip()

    # Remove Markdown JSON code fences
    clean_response = re.sub(
        r"^```(?:json)?\s*",
        "",
        clean_response,
        flags=re.IGNORECASE
    )

    clean_response = re.sub(
        r"\s*```$",
        "",
        clean_response
    )

    try:
        result = json.loads(clean_response)

    except json.JSONDecodeError:

        # Try to extract a JSON object if extra text was returned
        start = clean_response.find("{")

        if start == -1:
            raise ValueError(
                f"No JSON object found in response:\n{response.text}"
            )

        result, _ = json.JSONDecoder().raw_decode(
            clean_response[start:]
        )

    if not isinstance(result, dict):
        raise ValueError("The response must be a JSON object.")

    return result




def generate_json(client, prompt, model, config=None, max_retries=4):

    for attempt in range(max_retries):

        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config
            )

            # Convert Gemini response into a Python dictionary
            return parse_json_response(response)

        except errors.ServerError as e:

            if attempt == max_retries - 1:
                raise

            wait_time = 2 ** (attempt + 1)

            print(
                f"Gemini server error: {e}. "
                f"Retrying in {wait_time} seconds..."
            )

            time.sleep(wait_time)


        except errors.ServerError as e:

            if attempt == max_retries - 1:
                raise

            wait_time = 2 ** (attempt + 1)

            print(
                f"Gemini server error: {e}. "
                f"Retrying in {wait_time} seconds..."
            )

            time.sleep(wait_time)


def load_profile(profile_path):

    if not profile_path.exists():
        raise FileNotFoundError(
            f"Profile file not found: {profile_path}"
        )

    with open(profile_path, "r", encoding="utf-8") as file:
        profile = json.load(file)

    return profile


def normalize_list(value):

    if isinstance(value, list):
        return [str(item) for item in value if item is not None]

    if isinstance(value, str) and value.strip():
        return [value.strip()]

    return []


def normalize_boolean(value):

    if isinstance(value, bool):
        return value

    if isinstance(value, str):

        value = value.strip().lower()

        if value in ["true", "yes"]:
            return True

        if value in ["false", "no"]:
            return False

    return "unknown"


def show_list(title, items):

    st.markdown(f"**{title}**")

    items = normalize_list(items)

    if items:
        for item in items:
            st.markdown(f"- {item}")
    else:
        st.caption("No information available.")


# ============================================================
# 4. EXTRACT JOB INFORMATION
# ============================================================

def extract_job_information(
    client,
    job_description,
    model_name
):

    prompt = f"""
You are a job advertisement extraction assistant.

Read the following job advertisement:

{job_description}

Extract the following information:

- job title
- company
- location
- type of position
- employment type
- remote
- requirements
- skills

Rules:

- "remote" must be true if the job is fully remote / 100% online.
- "remote" must be false if the job requires on-site work or is hybrid.
- "remote" must be "unknown" if this cannot be determined.
- Do not confuse hybrid with fully remote.
- Do not invent missing information.
- Use "Not specified" for missing text fields.
- Use empty arrays for missing requirements or skills.

Return JSON using exactly these keys:

{{
    "job_title": "",
    "company": "",
    "location": "",
    "type_of_position": "",
    "employment_type": "",
    "remote": "unknown",
    "requirements": [],
    "skills": []
}}

Do not add any explanation outside the JSON.
"""

    job = generate_json(
        client,
        prompt,
        model_name
    )

    # Ensure all expected keys exist
    string_keys = [
        "job_title",
        "company",
        "location",
        "type_of_position",
        "employment_type"
    ]

    for key in string_keys:
        value = job.get(key, "Not specified")
        job[key] = str(value) if value is not None else "Not specified"

    job["remote"] = normalize_boolean(job.get("remote"))
    job["requirements"] = normalize_list(job.get("requirements"))
    job["skills"] = normalize_list(job.get("skills"))

    return job


# ============================================================
# 5. ANALYZE CANDIDATE-JOB MATCH
# ============================================================

def evaluate_job_match(
    client,
    job,
    profile,
    model_name,
    candidate_location,
    max_commute_hours
):

    prompt = f"""
You are a job-matching assistant.

Compare this job advertisement with this candidate profile.

JOB:
{json.dumps(job, indent=2, ensure_ascii=False)}

CANDIDATE PROFILE:
{json.dumps(profile, indent=2, ensure_ascii=False)}

Analyze:

1. Overall match percentage (integer from 0 to 100).
2. Strong matches.
3. Missing or weak requirements.
4. Relevant experience from candidate projects or education.
5. Important concerns or gaps.
6. An honest recommendation: Should the candidate apply?
7. Location and commuting suitability.

LOCATION RULES:

The candidate is based in {candidate_location}.

The maximum acceptable one-way commute is approximately
{max_commute_hours} hours by public transportation.

- If the job is fully remote and located in Germany,
  consider the location suitable.
- If the job requires on-site or hybrid work in Chemnitz,
  consider it suitable.
- For another on-site or hybrid location, mark it suitable
  only if the commute is reasonably known to be within
  approximately {max_commute_hours} hours.
- If the location is clearly farther away, mark it unsuitable.
- If the commuting time cannot be determined reliably,
  return "unknown".
- Do not invent exact travel times.
- Do not claim to have checked live train schedules.

IMPORTANT RULES:

- Do not invent skills, experience, education or qualifications.
- Only use information in the candidate profile.
- Distinguish between skills already acquired and skills
  currently being learned.
- Be honest about gaps.
- Match percentage is an estimate, not a guarantee.

Return JSON using exactly these keys:

{{
    "match_percentage": 0,
    "strong_matches": [],
    "missing_or_weak_requirements": [],
    "relevant_experience": [],
    "concerns_or_gaps": [],
    "recommendation": "",
    "remote": "unknown",
    "commute_suitable": "unknown",
    "location_reason": ""
}}

The values of remote and commute_suitable must be:
true, false, or "unknown".

Do not change the key names.
Do not add any other keys.
Do not add explanation outside the JSON.
"""

    recommendation = generate_json(
        client,
        prompt,
        model_name
    )

    # Clean and validate the returned information

    try:
        percentage = int(float(recommendation.get("match_percentage", 0)))
    except (ValueError, TypeError):
        percentage = 0

    recommendation["match_percentage"] = max(
        0,
        min(100, percentage)
    )

    list_keys = [
        "strong_matches",
        "missing_or_weak_requirements",
        "relevant_experience",
        "concerns_or_gaps"
    ]

    for key in list_keys:
        recommendation[key] = normalize_list(
            recommendation.get(key)
        )

    recommendation["recommendation"] = str(
        recommendation.get("recommendation", "")
    )

    # Use the extracted remote classification consistently
    recommendation["remote"] = job["remote"]

    recommendation["commute_suitable"] = normalize_boolean(
        recommendation.get("commute_suitable")
    )

    recommendation["location_reason"] = str(
        recommendation.get("location_reason", "")
    )

    return recommendation


# ============================================================
# 6. GENERATE COVER LETTER
# ============================================================

def generate_cover_letter(
    client,
    job,
    profile,
    model_name
):

    prompt = f"""
You are a professional job-cover-letter-writing assistant.

Write a tailored cover letter for this job using the candidate profile.

JOB:
{json.dumps(job, indent=2, ensure_ascii=False)}

CANDIDATE PROFILE:
{json.dumps(profile, indent=2, ensure_ascii=False)}

IMPORTANT RULES:

- Use only information contained in the candidate profile.
- Do not invent skills, experience, education or qualifications.
- Highlight relevant skills, education, projects and experience.
- Distinguish practical experience from skills currently being learned.
- Be honest about gaps.
- Do not invent company information or recipient names.
- Write a professional and natural cover letter.
- Avoid generic and exaggerated claims.

Return JSON using exactly this key:

{{
    "cover_letter": ""
}}

Put the complete cover letter inside "cover_letter".
Do not add any explanation outside the JSON.
"""

    result = generate_json(
        client,
        prompt,
        model_name
    )

    cover_letter = result.get("cover_letter", "")

    if not isinstance(cover_letter, str):
        raise ValueError("Invalid cover letter returned by Gemini.")

    return cover_letter.strip()


# ============================================================
# 7. COMPLETE JOB ANALYSIS WORKFLOW
# ============================================================

def analyze_job(
    client,
    job_description,
    profile_path,
    model_name,
    candidate_location,
    max_commute_hours
):

    # Load candidate profile
    profile = load_profile(profile_path)

    # Step 1: Extract job information
    job = extract_job_information(
        client,
        job_description,
        model_name
    )

    # Step 2: Compare candidate with job
    recommendation = evaluate_job_match(
        client,
        job,
        profile,
        model_name,
        candidate_location,
        max_commute_hours
    )

    # Step 3: Generate cover letter only if commute is suitable
    cover_letter = ""

    if recommendation["commute_suitable"] is True:

        cover_letter = generate_cover_letter(
            client,
            job,
            profile,
            model_name
        )

    # Combine everything into one dictionary
    job_result = {
        "job": job,
        "recommendation": recommendation,
        "cover_letter": cover_letter
    }

    return job_result


# ============================================================
# 8. STREAMLIT APPLICATION
# ============================================================

def main():

    st.set_page_config(
        page_title="ApplyWise AI",
        page_icon="💼",
        layout="wide"
    )

    st.title("💼 ApplyWise AI")

    st.write(
        "Your AI-powered job matching assistant. "
        "Analyze job advertisements, evaluate your suitability "
        "and generate tailored cover letters."
    )

    # --------------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------------

    with st.sidebar:

        st.header("Settings")

        candidate_location = st.text_input(
            "Your location",
            value=CANDIDATE_LOCATION
        )

        max_commute_hours = st.number_input(
            "Maximum commuting time (hours)",
            min_value=0.5,
            max_value=5.0,
            value=MAX_COMMUTE_HOURS,
            step=0.5
        )

        model_name = st.text_input(
            "Gemini model",
            value=MODEL_NAME
        )

        st.divider()

        st.subheader("Project status")

        if API_KEY:
            st.success("Gemini API key found")
        else:
            st.error("Gemini API key missing")

        if PROFILE_PATH.exists():
            st.success("Candidate profile found")
        else:
            st.error("Candidate profile missing")

    # --------------------------------------------------------
    # JOB ADVERTISEMENT INPUT
    # --------------------------------------------------------

    st.header("1. Job advertisement")

    job_text = st.text_area(
        "Paste the complete job advertisement below:",
        height=320,
        placeholder="Paste the complete job advertisement here..."
    )

    analyze_button = st.button(
        "Analyze job",
        type="primary",
        disabled=not job_text.strip()
    )

    # --------------------------------------------------------
    # RUN ANALYSIS
    # --------------------------------------------------------

    if analyze_button:

        try:

            client = get_gemini_client(API_KEY)

            with st.spinner(
                "Analyzing the job advertisement..."
            ):

                result = analyze_job(
                    client=client,
                    job_description=job_text,
                    profile_path=PROFILE_PATH,
                    model_name=model_name.strip(),
                    candidate_location=candidate_location.strip(),
                    max_commute_hours=float(max_commute_hours)
                )

            st.session_state["latest_result"] = result
            st.success("Job analysis completed successfully!")

        except Exception as exc:

            st.error("The analysis could not be completed.")

            st.exception(exc)

    # --------------------------------------------------------
    # DISPLAY RESULTS
    # --------------------------------------------------------

    result = st.session_state.get("latest_result")

    if result:

        job = result["job"]

        recommendation = result["recommendation"]

        st.divider()

        st.header(
            job.get("job_title") or "Job analysis"
        )

        # ----------------------------------------------------
        # JOB OVERVIEW
        # ----------------------------------------------------

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Match percentage",
            f'{recommendation["match_percentage"]}%'
        )

        col2.metric(
            "Company",
            job.get("company") or "Not specified"
        )

        col3.metric(
            "Location",
            job.get("location") or "Not specified"
        )

        # ----------------------------------------------------
        # EXTRACTED JOB INFORMATION
        # ----------------------------------------------------

        st.subheader("2. Extracted job information")

        st.write(
            f'**Position:** {job.get("type_of_position")}'
        )

        st.write(
            f'**Employment type:** {job.get("employment_type")}'
        )

        st.write(
            f'**Remote:** {job.get("remote")}'
        )

        col1, col2 = st.columns(2)

        with col1:

            show_list(
                "Requirements",
                job.get("requirements", [])
            )

        with col2:

            show_list(
                "Skills",
                job.get("skills", [])
            )

        # ----------------------------------------------------
        # CANDIDATE-JOB MATCH
        # ----------------------------------------------------

        st.divider()

        st.header("3. Candidate-job match")

        st.subheader("Recommendation")

        st.write(
            recommendation.get(
                "recommendation",
                "No recommendation returned."
            )
        )

        left, right = st.columns(2)

        with left:

            show_list(
                "Strong matches",
                recommendation.get("strong_matches", [])
            )

            show_list(
                "Relevant experience",
                recommendation.get("relevant_experience", [])
            )

        with right:

            show_list(
                "Missing or weak requirements",
                recommendation.get("missing_or_weak_requirements", [])
            )

            show_list(
                "Concerns or gaps",
                recommendation.get("concerns_or_gaps", [])
            )

        # ----------------------------------------------------
        # LOCATION AND COMMUTING
        # ----------------------------------------------------

        st.divider()

        st.header("4. Location and commuting")

        col1, col2 = st.columns(2)

        col1.metric(
            "Remote",
            str(recommendation.get("remote", "unknown"))
        )

        col2.metric(
            "Commute suitable",
            str(recommendation.get("commute_suitable", "unknown"))
        )

        st.write(
            recommendation.get(
                "location_reason",
                "No location explanation returned."
            )
        )

        # ----------------------------------------------------
        # COVER LETTER
        # ----------------------------------------------------

        st.divider()

        st.header("5. Cover letter")

        cover_letter = result.get("cover_letter")

        if cover_letter:

            edited_cover_letter = st.text_area(
                "Generated cover letter (you can edit it):",
                value=cover_letter,
                height=420,
                key="cover_letter_editor"
            )

            st.download_button(
                label="Download cover letter (.txt)",
                data=edited_cover_letter,
                file_name="cover_letter.txt",
                mime="text/plain"
            )

        else:

            st.info(
                "A cover letter was not generated because the "
                "commuting suitability was not confirmed as True. "
                "You can review the job and its location assessment."
            )

        # ----------------------------------------------------
        # JSON OUTPUT
        # ----------------------------------------------------

        with st.expander("View complete results (JSON)"):

            st.json(result)


# ============================================================
# 9. RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    main()
