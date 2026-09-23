import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import Resume, StudentProfile, Job, User
from schemas import ResumeResponse, JobResponse
from auth import get_current_user
from ai_service import generate_resume, _chat_with_gemini, find_matching_jobs

logger = logging.getLogger("careerhub.ai")

router = APIRouter(prefix="/ai", tags=["AI"])


class GenerateResumeRequest(BaseModel):
    pass


class ResumeChatRequest(BaseModel):
    message: str
    history: list[dict[str, str]] = []


class JobRecommendation(BaseModel):
    job: JobResponse
    match_score: float


async def _get_student_profile(user: User, db: AsyncSession) -> StudentProfile:
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )
    return profile


@router.post("/generate-resume/")
async def generate_resume_endpoint(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can generate resumes",
        )

    profile = await _get_student_profile(user, db)
    resume_data = await generate_resume(profile)
    return resume_data


@router.post("/create-resume/", response_model=ResumeResponse)
async def create_resume_endpoint(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can create resumes",
        )

    profile = await _get_student_profile(user, db)
    resume_data = await generate_resume(profile)

    skills = resume_data.get("skills", [])
    if isinstance(skills, list):
        skills = json.dumps(skills)

    resume = Resume(
        student_id=profile.id,
        title=resume_data.get("title", "AI Generated Resume"),
        about=resume_data.get("about", ""),
        skills=skills,
        schedule_type=resume_data.get("schedule_type", "flexible"),
        work_format=resume_data.get("work_format", "online"),
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return resume


@router.post("/resume-chat/")
async def resume_chat_endpoint(
    request: ResumeChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can use the resume chat",
        )

    messages = request.history + [{"role": "user", "content": request.message}]

    raw_response = await _chat_with_gemini(messages)

    from ai_service import _strip_code_fences

    try:
        parsed = json.loads(_strip_code_fences(raw_response))
        ai_message = parsed.get("message", "I couldn't process that.")
        resume_data = parsed.get("resume_data")
    except (json.JSONDecodeError, TypeError):
        ai_message = _strip_code_fences(raw_response)
        resume_data = None

    return {"message": ai_message, "resume_data": resume_data}


@router.get("/recommend-jobs/")
async def recommend_jobs_endpoint(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can get job recommendations",
        )

    profile = await _get_student_profile(user, db)

    result = await db.execute(
        select(Resume).where(Resume.student_id == profile.id)
    )
    resumes = list(result.scalars().all())

    matched = await find_matching_jobs(profile, resumes, db)

    recommendations = []
    for item in matched:
        job = item["job"]
        try:
            job_resp = JobResponse.model_validate(job)
        except Exception:
            continue
        payload = job_resp.model_dump()
        payload["match_score"] = item["match_score"]
        recommendations.append(payload)

    return recommendations
