import json
import os
import re
import logging
from typing import Any

try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import StudentProfile, Resume, Job

try:
    from config import settings as _settings
except Exception:  # pragma: no cover
    _settings = None

logger = logging.getLogger("careerhub.ai")


def _get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key and _settings is not None:
        key = getattr(_settings, "GEMINI_API_KEY", "") or ""
    return key.strip()

SKILL_SUGGESTIONS = {
    "programming": [
        "Python", "JavaScript", "TypeScript", "Java", "C++", "Go", "Rust",
        "SQL", "HTML/CSS", "React", "Vue.js", "Node.js", "Django", "FastAPI",
        "Git", "Docker", "Linux", "REST API", "PostgreSQL", "MongoDB",
    ],
    "design": [
        "Figma", "Adobe Photoshop", "Adobe Illustrator", "UI/UX Design",
        "Prototyping", "Wireframing", "User Research", "Adobe XD",
        "Sketch", "InVision", "Responsive Design", "Typography",
    ],
    "marketing": [
        "SEO", "Google Analytics", "Social Media Marketing", "Content Marketing",
        "Email Marketing", "Google Ads", "Facebook Ads", "Copywriting",
        "A/B Testing", "Marketing Strategy", "Brand Management", "CRM",
    ],
    "data": [
        "Data Analysis", "Machine Learning", "SQL", "Python", "R",
        "Tableau", "Power BI", "Excel", "Statistics", "Pandas", "NumPy",
        "Scikit-learn", "TensorFlow", "Deep Learning", "ETL",
    ],
    "business": [
        "Project Management", "Agile/Scrum", "Leadership", "Communication",
        "Problem Solving", "Team Management", "Strategic Planning",
        "Financial Analysis", "Stakeholder Management", "Risk Assessment",
    ],
    "finance": [
        "Financial Analysis", "Accounting", "Excel", "SAP", "Bloomberg Terminal",
        "Financial Modeling", "Budgeting", "Forecasting", "IFRS/GAAP",
        "Risk Management", "Portfolio Management", "SQL",
    ],
    "general": [
        "Communication", "Teamwork", "Problem Solving", "Time Management",
        "Critical Thinking", "Adaptability", "Creativity", "Leadership",
        "Attention to Detail", "MS Office", "English", "Russian",
    ],
}

CATEGORY_KEYWORDS = {
    "programming": [
        "programming", "developer", "software", "backend", "frontend", "fullstack",
        "web", "mobile", "devops", "engineer", "coder", "it",
    ],
    "design": [
        "design", "designer", "ui", "ux", "graphic", "creative", "art",
        "visual", "illustration", "brand",
    ],
    "marketing": [
        "marketing", "seo", "advertising", "content", "social media", "pr",
        "brand", "digital marketing", "growth",
    ],
    "data": [
        "data", "analytics", "machine learning", "ai", "science",
        "data engineer", "data analyst", "ml engineer",
    ],
    "business": [
        "business", "management", "consulting", "strategy", "operations",
        "project manager", "product manager", "analyst",
    ],
    "finance": [
        "finance", "banking", "investment", "accounting", "audit",
        "financial", "trader", "risk",
    ],
    "general": [
        "assistant", "intern", "junior", "trainee", "office", "reception",
        "sales", "customer", "support", "call center",
    ],
}

RESUME_CHAT_SYSTEM_PROMPT = """You are an AI resume builder assistant for students. Your goal is to help students create professional resumes.

Ask the student one question at a time:
1. What position are you applying for?
2. What are your skills (technologies, tools, languages)?
3. What is your experience (internships, projects, hackathons)?
4. What schedule suits you (flexible, 2-4 hours, full-time)?
5. What work format do you prefer (online, offline, hybrid)?

When responding, you MUST return valid JSON in this exact format:
{
    "message": "Your conversational response to the student",
    "ready": false,
    "resume_data": null
}

Rules:
- Until you have answers to ALL five questions above, always respond with "ready": false, "resume_data": null and ask the NEXT question only (one question per message).
- Never include resume data or say the resume is ready before all questions are answered. Do not invent skills or experience for the student.
- Only when all five answers are collected, set "ready": true and fill resume_data:
{
    "title": "Resume title based on student's field",
    "about": "Professional summary paragraph",
    "skills": ["skill1", "skill2", "skill3"],
    "schedule_type": "full-time or part-time or flexible",
    "work_format": "online or offline or hybrid"
}
- When ready is true, "message" should be short: the resume is ready, ask the student to save it. Ask no new questions.
- Keep the about section professional and concise (2-3 sentences)
- Suggest 5-8 relevant skills based on the student's field
- Be friendly and encouraging in your messages
- Respond in the same language the student uses
"""

CAREER_CHAT_SYSTEM_PROMPT = """You are a friendly AI career consultant for CareerHub.
You help students and job seekers with:
- resume and CV advice
- job search strategy
- interview preparation
- salary and career growth questions

Rules:
- Reply with plain conversational text only (no JSON, no markdown code fences).
- Be concise, practical and encouraging.
- Respond in the same language the user uses.
- If you do not know something, say so honestly.
"""


def _strip_code_fences(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_-]*\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def _build_user_profile(student_profile: StudentProfile) -> dict[str, Any]:
    user = student_profile.user
    profile = {
        "full_name": f"{user.first_name} {user.last_name}".strip() or user.username,
        "email": user.email,
        "phone": user.phone or "",
        "university": student_profile.university or "",
        "faculty": student_profile.faculty or "",
        "course": student_profile.course,
        "city": student_profile.city or "",
        "age": student_profile.age,
        "category": "general",
    }

    faculty_lower = (student_profile.faculty or "").lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in faculty_lower for kw in keywords):
            profile["category"] = category
            break

    return profile


def _generate_resume_rule_based(student_profile: StudentProfile) -> dict[str, Any]:
    profile = _build_user_profile(student_profile)
    category = profile["category"]
    skills = SKILL_SUGGESTIONS.get(category, SKILL_SUGGESTIONS["general"])[:8]

    parts = []
    if profile["university"]:
        parts.append(profile["university"])
    if profile["faculty"]:
        parts.append(profile["faculty"])
    title = " | ".join(parts) if parts else "Student Resume"

    about_parts = []
    if profile["university"]:
        about_parts.append(f"Student at {profile['university']}")
    if profile["faculty"]:
        about_parts.append(f"studying {profile['faculty']}")
    if profile["city"]:
        about_parts.append(f"based in {profile['city']}")
    about = " ".join(about_parts) + "." if about_parts else "Motivated student looking for opportunities."

    return {
        "title": title,
        "about": about,
        "skills": skills,
        "schedule_type": "flexible",
        "work_format": "online",
        "category": category,
    }


async def generate_resume(student_profile: StudentProfile) -> dict[str, Any]:
    api_key = _get_api_key()
    if not api_key or not GEMINI_AVAILABLE:
        logger.info("Gemini unavailable, using rule-based resume generation")
        return _generate_resume_rule_based(student_profile)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        profile = _build_user_profile(student_profile)
        prompt = f"""Generate a professional resume for a student with this profile:
Name: {profile['full_name']}
University: {profile['university']}
Faculty/Faculty: {profile['faculty']}
City: {profile['city']}
Detected category: {profile['category']}

Return ONLY valid JSON in this format:
{{
    "title": "Professional resume title",
    "about": "2-3 sentence professional summary",
    "skills": ["skill1", "skill2", ...],
    "schedule_type": "full-time or part-time or flexible",
    "work_format": "online or offline or hybrid"
}}

Skills should be relevant to the student's field ({profile['category']}). Include 6-8 skills."""

        response = model.generate_content(prompt)
        text = response.text.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return _generate_resume_rule_based(student_profile)
    except Exception as e:
        logger.warning(f"Gemini generation failed, falling back to rule-based: {e}")
        return _generate_resume_rule_based(student_profile)


async def _chat_with_gemini(
    messages: list[dict[str, str]],
    system_prompt: str = RESUME_CHAT_SYSTEM_PROMPT,
) -> str:
    api_key = _get_api_key()
    if not api_key or not GEMINI_AVAILABLE:
        if system_prompt == RESUME_CHAT_SYSTEM_PROMPT:
            return json.dumps({
                "message": "AI is currently unavailable. Please try again later or create your resume manually.",
                "ready": False,
                "resume_data": None,
            })
        return (
            "ИИ сейчас недоступен. Попробуйте позже или создайте резюме вручную."
        )

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            system_instruction=system_prompt,
        )

        history = []
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})

        chat = model.start_chat(history=history)
        response = chat.send_message(messages[-1]["content"])
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini chat failed: {e}")
        if system_prompt == RESUME_CHAT_SYSTEM_PROMPT:
            return json.dumps({
                "message": "Sorry, an error occurred. Please try again.",
                "ready": False,
                "resume_data": None,
            })
        return "Произошла ошибка при обращении к ИИ. Попробуйте ещё раз."


async def find_matching_jobs(
    student_profile: StudentProfile,
    resumes: list[Resume],
    db: AsyncSession,
    limit: int = 10,
) -> list[dict[str, Any]]:
    profile = _build_user_profile(student_profile)
    category = profile["category"]

    all_skills = set()
    for resume in resumes:
        if resume.skills:
            if isinstance(resume.skills, list):
                all_skills.update(resume.skills)
            elif isinstance(resume.skills, str):
                try:
                    parsed = json.loads(resume.skills)
                    if isinstance(parsed, list):
                        all_skills.update(parsed)
                except (json.JSONDecodeError, TypeError):
                    pass

    result = await db.execute(
        select(Job).where(Job.is_active == True)
    )
    jobs = result.scalars().all()

    scored_jobs = []
    for job in jobs:
        score = 0.0
        job_text = f"{job.title} {job.description or ''}".lower()

        if category != "general":
            category_kw = CATEGORY_KEYWORDS.get(category, [])
            matches = sum(1 for kw in category_kw if kw in job_text)
            score += min(matches * 15, 45)

        if all_skills:
            skill_matches = sum(
                1 for skill in all_skills if skill.lower() in job_text
            )
            score += min(skill_matches * 8, 30)

        if profile["city"] and job.location_address:
            if profile["city"].lower() in job.location_address.lower():
                score += 10

        if job.work_format and profile.get("work_format"):
            if str(profile["work_format"]).lower() in str(job.work_format).lower():
                score += 5

        if score > 0:
            scored_jobs.append({"job": job, "match_score": min(round(score, 1), 100)})

    scored_jobs.sort(key=lambda x: x["match_score"], reverse=True)
    return scored_jobs[:limit]
