from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from typing import Optional
from io import BytesIO

from database import get_db
from models import (
    Job, Resume, Application, Favorite, Category,
    StudentProfile, EmployerProfile, User, Notification,
)
from schemas import (
    JobResponse, ResumeResponse, ApplicationResponse,
    UserResponse, StudentProfileResponse, EmployerProfileResponse,
    NotificationResponse,
)
from auth import get_current_user, require_verified_email

router = APIRouter(tags=["Jobs"])


@router.get("/jobs/")
async def list_jobs(
    category: Optional[str] = None,
    schedule: Optional[str] = None,
    work_format: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
):
    query = select(Job).where(Job.is_active == True)

    if category:
        query = query.join(Category).where(Category.slug == category)
    if schedule:
        query = query.where(Job.schedule == schedule)
    if work_format:
        query = query.where(Job.work_format == work_format)
    if search:
        query = query.where(
            or_(Job.title.ilike(f"%{search}%"), Job.description.ilike(f"%{search}%"))
        )

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(Job.created_at.desc()).offset((page - 1) * 10).limit(10)
    result = await db.execute(query)
    jobs = result.scalars().all()

    return {
        "count": total,
        "page": page,
        "results": [
            {
                "id": j.id,
                "title": j.title,
                "description": j.description,
                "salary_min": j.salary_min,
                "salary_max": j.salary_max,
                "schedule": j.schedule,
                "work_format": j.work_format,
                "min_age": j.min_age,
                "experience_required": j.experience_required,
                "is_active": j.is_active,
                "location_address": j.location_address,
                "source": j.source,
                "created_at": j.created_at.isoformat() if j.created_at else "",
            }
            for j in jobs
        ],
    }


@router.get("/jobs/{job_id}/")
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    employer = None
    if job.employer_id:
        emp_result = await db.execute(select(EmployerProfile).where(EmployerProfile.id == job.employer_id))
        employer = emp_result.scalar_one_or_none()

    return {
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "schedule": job.schedule,
        "work_format": job.work_format,
        "min_age": job.min_age,
        "experience_required": job.experience_required,
        "is_active": job.is_active,
        "location_address": job.location_address,
        "location_lat": job.location_lat,
        "location_lng": job.location_lng,
        "source": job.source,
        "source_url": job.source_url,
        "created_at": job.created_at.isoformat() if job.created_at else "",
        "employer": {
            "id": employer.id,
            "company_name": employer.company_name,
            "description": employer.description,
            "website": employer.website,
            "address": employer.address,
        } if employer else None,
    }


@router.get("/categories/")
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category))
    cats = result.scalars().all()
    return [{"id": c.id, "name": c.name, "slug": c.slug} for c in cats]


@router.get("/users/me/")
async def get_me(user: User = Depends(require_verified_email)):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "phone": user.phone,
        "avatar": user.avatar,
        "location": user.location,
        "is_email_verified": user.is_email_verified,
        "current_plan": user.current_plan,
    }


@router.post("/favorites/add/")
async def add_favorite(
    data: dict,
    user: User = Depends(require_verified_email),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only for students")

    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")

    job_id = data.get("job_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id required")

    result = await db.execute(
        select(Favorite).where(
            Favorite.student_id == profile.id, Favorite.job_id == job_id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already in favorites")

    fav = Favorite(student_id=profile.id, job_id=job_id)
    db.add(fav)
    await db.commit()
    return {"detail": "Added to favorites"}


@router.get("/favorites/")
async def list_favorites(
    user: User = Depends(require_verified_email),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        return []

    result = await db.execute(
        select(Favorite).where(Favorite.student_id == profile.id)
    )
    favs = result.scalars().all()

    jobs = []
    for fav in favs:
        job_result = await db.execute(select(Job).where(Job.id == fav.job_id))
        job = job_result.scalar_one_or_none()
        if job:
            jobs.append({
                "id": job.id,
                "title": job.title,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "created_at": job.created_at.isoformat() if job.created_at else "",
            })
    return jobs


@router.post("/applications/")
async def create_application(
    data: dict,
    user: User = Depends(require_verified_email),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only for students")

    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")

    job_id = data.get("job_id")
    resume_id = data.get("resume_id")
    cover_letter = data.get("cover_letter", "")

    if not job_id or not resume_id:
        raise HTTPException(status_code=400, detail="job_id and resume_id required")

    result = await db.execute(
        select(Application).where(
            Application.job_id == job_id, Application.resume_id == resume_id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already applied")

    app = Application(
        job_id=job_id,
        resume_id=resume_id,
        cover_letter=cover_letter,
        status="sent",
    )
    db.add(app)
    await db.commit()
    return {"detail": "Application created", "id": app.id}


@router.get("/applications/")
async def list_applications(
    user: User = Depends(require_verified_email),
    db: AsyncSession = Depends(get_db),
):
    if user.role == "student":
        result = await db.execute(
            select(StudentProfile).where(StudentProfile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            return []
        result = await db.execute(
            select(Application).where(Application.resume_id.in_(
                select(Resume.id).where(Resume.student_id == profile.id)
            ))
        )
    elif user.role == "employer":
        result = await db.execute(
            select(EmployerProfile).where(EmployerProfile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            return []
        result = await db.execute(
            select(Application).where(Application.job_id.in_(
                select(Job.id).where(Job.employer_id == profile.id)
            ))
        )
    else:
        return []

    apps = result.scalars().all()
    return [
        {
            "id": a.id,
            "job_id": a.job_id,
            "resume_id": a.resume_id,
            "status": a.status,
            "cover_letter": a.cover_letter,
            "created_at": a.created_at.isoformat() if a.created_at else "",
        }
        for a in apps
    ]


@router.get("/notifications/")
async def list_notifications(
    user: User = Depends(require_verified_email),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    notifs = result.scalars().all()
    return [
        {
            "id": n.id,
            "notification_type": n.notification_type,
            "title": n.title,
            "message": n.message,
            "link": n.link,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else "",
        }
        for n in notifs
    ]


@router.get("/notifications/unread-count/")
async def unread_count(
    user: User = Depends(require_verified_email),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user.id, Notification.is_read == False
        )
    )
    count = result.scalar() or 0
    return {"unread_count": count}
