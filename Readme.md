
# ApplyWise AI

**An AI-powered job application assistant that helps candidates evaluate job opportunities and generate tailored cover letters.**

ApplyWise AI analyzes job advertisements against a candidate's skills, qualifications, experience, and location. It provides a structured assessment of job suitability and helps candidates make more informed application decisions.

## Features

- **Job Description Analysis:** Extracts key information, including job title, company, location, employment type, remote-work options, responsibilities, qualifications, and required skills.
- **Candidate–Job Matching:** Compares job requirements with the candidate's profile and calculates a match score from 0 to 100.
- **Strengths and Skill Gaps:** Identifies relevant experience, matching qualifications, missing requirements, and potential concerns.
- **Application Recommendation:** Provides a recommendation based on the candidate–job match.
- **Location and Commuting Assessment:** Evaluates remote-work suitability and commuting considerations.
- **AI-Generated Cover Letters:** Generates personalized cover letters for suitable positions.
- **Downloadable Results:** Allows users to download generated cover letters.

## How It Works

1. **Submit a job description:** Paste a job advertisement into the application.
2. **Analyze the position:** Extract relevant job details, responsibilities, and requirements.
3. **Evaluate the match:** Compare the extracted requirements with the candidate's profile.
4. **Review the assessment:** Explore the match score, strengths, skill gaps, concerns, and recommendation.
5. **Assess location suitability:** Evaluate remote-work arrangements and commuting considerations.
6. **Generate a cover letter:** Create a tailored cover letter for suitable positions.
7. **Download the result:** Download the generated cover letter for review and further editing.

## Technology Stack

- **Python** – Application logic and workflow
- **Streamlit** – Interactive web interface
- **Google Gemini API** – Job analysis, candidate–job matching, and cover letter generation
- **JSON** – Structured data and candidate profile
- **Git & GitHub** – Version control and project management

## Project Structure

```text
ApplyWise-AI/
│
├── app.py
├── main.py
├── profile_example.json
├── requirements.txt
├── .env.example
├── .gitignore
└── Readme.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd ApplyWise-AI
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API key

Create a local `.env` file based on `.env.example`.

Add your Google Gemini API key:

```text
GEMINI_API_KEY=your_actual_api_key
```

Never commit your actual `.env` file or expose your API key.

### 5. Configure the candidate profile

Use `profile-example.json` as a template and create your own local candidate profile.

Review and update the information before using the application.

### 6. Run the application

```bash
streamlit run app.py
```

## Important Notes

- Never upload or commit `.env` files containing API credentials.
- Keep personal candidate information private.
- Review and correct the candidate profile before using it for applications.
- AI-generated match scores and cover letters are suggestions, not guarantees.
- Verify all information in generated cover letters before submitting applications.
- Gemini model availability depends on the Google GenAI API.

## Project Status

ApplyWise AI is under active development. Features and functionality may evolve as the project improves.
