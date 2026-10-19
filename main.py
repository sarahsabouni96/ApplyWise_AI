

import os
import json
from google import genai



# Step 1: Read the job advertisement from the terminal
print("\nPaste the complete job advertisement below.")
print("When you finish, type END on a new line and press Enter.\n")

job_description = []

while True:
    line = input()

    if line.strip() == "END":
        break

    job_description.append(line)

x = "\n".join(job_description)

if not x.strip():
    print("No job description was entered. Please try again.")
    raise SystemExit

print("\nJob advertisement received successfully!")
print(f"Characters received: {len(x)}")

jobs = []



api_key = os.getenv("GEMINI_API_KEY")

print(api_key is not None)

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents=f"""
Here is a job advertisement:

{x}

Extract the following information:
- job title
- company
- location
- type of position
- requirements
- skills
- "remote" must be true if the job is fully remote/100% online,
  false if it requires on-site work or is hybrid,
  and "unknown" if this cannot be determined.

Return the result as JSON.
Return JSON using exactly these keys:
"job_title"
"company"
"location"
"type_of_position"
"employment_type"
"remote"
"requirements"
"skills"
Do not add any explanation outside the JSON.
"""
)

print(response.text)
clean_response = response.text.replace("```json", "").replace("```", "").strip()

job = json.loads(clean_response)


print(job)
print(type(job))
print(job.keys())
print(job["job_title"])
print(job["skills"])


with open('profile-example.json') as profile-example_file:
    profile = json.load(profile-example_file)
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=f"""
You are a job-matching assistant.

Compare this job advertisement with this candidate profile.

JOB:
{json.dumps(job, indent=2)}

CANDIDATE PROFILE:
{json.dumps(profile, indent=2)}

Analyze:

1. Overall match percentage
2. Strong matches
3. Missing or weak requirements
4. Relevant experience from the candidate's projects or education
5. Important concerns or gaps
6. A short honest recommendation: Should the candidate apply?
7. Location and commuting suitability

For location and commuting:

- The candidate is based in Chemnitz, Germany.
- If the job is fully remote/100% online and the job is in Germany, consider the location suitable.
- If the job requires working on-site or hybrid, determine whether the workplace appears reasonably reachable from Chemnitz within approximately 1.5 hours by public transportation.
- If the location appears to be more than approximately 1.5 hours away, mark it as unsuitable.
- If you cannot determine the commuting time reliably, return "unknown" rather than inventing a travel time.
- Do not invent an exact travel time.

Important rules:
- Do not invent skills, experience, education, or qualifications.
- Only use information contained in the candidate profile.
- Distinguish between skills the candidate has and skills they are currently learning.
- Be honest about gaps.

Return the result as JSON.
Return the result as JSON using exactly these keys:

{{
    "match_percentage": number,
    "strong_matches": [],
    "missing_or_weak_requirements": [],
    "relevant_experience": [],
    "concerns_or_gaps": [],
    "recommendation": "",
    "remote": true/false/unknown,
    "commute_suitable": true/false/unknown,
    "location_reason": ""
}}

Do not change the key names.
Do not add any other keys.
Do not add any explanation outside the JSON.
"""
)

print(response.text)

clean_response2 = response.text.replace("```json", "").replace("```", "").strip()



recommendation = json.loads(clean_response2)
print(recommendation)
if recommendation["commute_suitable"] is True:
    print("Keep this job")
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=f"""
    You are a job-cover-letter-writing assistant.
    
    Write a tailored cover letter for this job using the candidate profile.
    
    JOB:
    {json.dumps(job, indent=2)}
    
    CANDIDATE PROFILE:
    {json.dumps(profile, indent=2)}
    
    Important rules:
    - Use only information contained in the candidate profile.
    - Do not invent skills, experience, education, or qualifications.
    - Highlight the candidate's most relevant skills, education, projects, and experience for this specific job.
    - Be honest about gaps.
    - Write a professional and natural cover letter.
    - Do not use generic claims that are not supported by the profile.
    
    Return the result as JSON using exactly this key:
    
    {{
        "cover_letter": ""
    }}
    
    Put the complete cover letter inside "cover_letter".
    Do not add any explanation outside the JSON.
    """
    )
    print(response.text)
    clean_response3 = response.text.replace("```json", "").replace("```", "").strip()

    cover_letter_result = json.loads(clean_response3)

    cover_letter = cover_letter_result["cover_letter"]
    job_result= {
        "job": job, 
        "recommendation" : recommendation,
        "cover_letter": cover_letter
    }
jobs.append(job_result)    
for job_result in jobs:
    print(job_result["job"]["job_title"])
    print(job_result["recommendation"]["match_percentage"])
    print(job_result["cover_letter"])
    
for job_result in jobs:
    print(job_result["job"]["job_title"])
    print(job_result["recommendation"]["match_percentage"])
    print(job_result["cover_letter"])