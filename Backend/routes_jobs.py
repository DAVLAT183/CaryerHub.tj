from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models import (
    Resume, Job, Application, StudentProfile, EmployerProfile,
    Category, Favorite, Notification, User,
)
from schemas import (
    ResumeCreateSchema, ResumeResponse, JobCreateSchema, JobResponse,
    ApplicationCreateSchema, ApplicationSchema,
)
from auth import get_current_user, get_optional_user

router = APIRouter(prefix="/api", tags=["Jobs"])


class ApplicationStatusUpdate(BaseModel):
    status: str


async def _get_student_profile(user: User, db: AsyncSession) -> StudentProfile:
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return profile


async def _get_employer_profile(user: User, db: AsyncSession) -> EmployerProfile:
    result = await db.execute(
        select(EmployerProfile).where(EmployerProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Employer profile not found")
    return profile


async def _serialize_resume(resume: Resume, db: AsyncSession) -> dict:
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.id == resume.student_id)
    )
    student = result.scalar_one_or_none()
    user_data = None
    if student:
        user_result = await db.execute(
            select(User).where(User.id == student.user_id)
        )
        user_obj = user_result.scalar_one_or_none()
        if user_obj:
            user_data = {
                "id": user_obj.id,
                "username": user_obj.username,
                "email": user_obj.email,
                "first_name": user_obj.first_name,
                "last_name": user_obj.last_name,
                "role": user_obj.role,
                "phone": user_obj.phone,
                "avatar": user_obj.avatar,
                "location": user_obj.location,
                "student_profile_id": student.id,
            }
    return {
        "id": resume.id,
        "student": {
            "id": student.id if student else 0,
            "user": user_data,
            "university": student.university if student else "",
            "faculty": student.faculty if student else "",
            "course": student.course if student else None,
            "birth_date": student.birth_date if student else None,
            "age": student.age if student else None,
            "city": student.city if student else "",
        } if student else None,
        "title": resume.title,
        "about": resume.about,
        "skills": resume.skills,
        "schedule_type": resume.schedule_type,
        "work_format": resume.work_format,
        "github_url": resume.github_url,
        "portfolio_url": resume.portfolio_url,
        "linkedin_url": resume.linkedin_url,
        "style": resume.style,
        "created_at": resume.created_at.isoformat() if resume.created_at else None,
        "updated_at": resume.updated_at.isoformat() if resume.updated_at else None,
    }


async def _serialize_employer(employer: EmployerProfile, db: AsyncSession) -> dict:
    user_result = await db.execute(
        select(User).where(User.id == employer.user_id)
    )
    user_obj = user_result.scalar_one_or_none()
    return {
        "id": employer.id,
        "user": {
            "id": user_obj.id,
            "username": user_obj.username,
            "email": user_obj.email,
            "first_name": user_obj.first_name,
            "last_name": user_obj.last_name,
            "role": user_obj.role,
            "phone": user_obj.phone,
            "avatar": user_obj.avatar,
            "location": user_obj.location,
        } if user_obj else None,
        "company_name": employer.company_name,
        "description": employer.description,
        "website": employer.website,
        "address": employer.address,
        "is_verified": employer.is_verified,
    }


async def _serialize_job(job: Job, db: AsyncSession, applications_count: int = 0) -> dict:
    employer = None
    if job.employer_id:
        emp_result = await db.execute(
            select(EmployerProfile).where(EmployerProfile.id == job.employer_id)
        )
        emp = emp_result.scalar_one_or_none()
        if emp:
            employer = await _serialize_employer(emp, db)

    category = None
    if job.category_id:
        cat_result = await db.execute(
            select(Category).where(Category.id == job.category_id)
        )
        cat = cat_result.scalar_one_or_none()
        if cat:
            category = {"id": cat.id, "name": cat.name, "slug": cat.slug}

    return {
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "min_age": job.min_age,
        "schedule": job.schedule,
        "work_format": job.work_format,
        "experience_required": job.experience_required,
        "is_active": job.is_active,
        "image": job.image,
        "image_url": job.image or None,
        "location_lat": job.location_lat,
        "location_lng": job.location_lng,
        "location_address": job.location_address,
        "has_location": job.location_lat is not None and job.location_lng is not None,
        "is_favorited": False,
        "source": job.source,
        "source_url": job.source_url,
        "source_id": job.source_id,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "applications_count": applications_count,
        "category": category,
        "category_name": category["name"] if category else None,
        "employer": employer,
    }


async def _serialize_application(app: Application, db: AsyncSession) -> dict:
    job_result = await db.execute(select(Job).where(Job.id == app.job_id))
    job = job_result.scalar_one_or_none()
    resume_result = await db.execute(select(Resume).where(Resume.id == app.resume_id))
    resume = resume_result.scalar_one_or_none()

    job_data = await _serialize_job(job, db) if job else None

    resume_data = None
    student_name = None
    if resume:
        resume_data = await _serialize_resume(resume, db)
        student_data = resume_data.get("student")
        if student_data and student_data.get("user"):
            u = student_data["user"]
            student_name = f"{u.get('first_name', '')} {u.get('last_name', '')}".strip() or u.get("username", "")

    job_employer_name = None
    if job_data and job_data.get("employer"):
        job_employer_name = job_data["employer"].get("company_name")

    return {
        "id": app.id,
        "job": job_data,
        "job_title": job.title if job else None,
        "job_employer_name": job_employer_name,
        "resume": resume_data,
        "student_name": student_name,
        "status": app.status,
        "cover_letter": app.cover_letter,
        "created_at": app.created_at.isoformat() if app.created_at else None,
    }


# ──────────────────────────── RESUMES ────────────────────────────


@router.get("/resumes/")
async def list_resumes(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role == "student":
        profile = await _get_student_profile(user, db)
        result = await db.execute(
            select(Resume).where(Resume.student_id == profile.id)
        )
    else:
        result = await db.execute(select(Resume))

    resumes = result.scalars().all()
    return [await _serialize_resume(r, db) for r in resumes]


@router.get("/resumes/{resume_id}/")
async def get_resume(
    resume_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return await _serialize_resume(resume, db)


@router.post("/resumes/")
async def create_resume(
    data: ResumeCreateSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can create resumes")

    profile = await _get_student_profile(user, db)

    resume = Resume(
        student_id=profile.id,
        title=data.title,
        about=data.about or "",
        skills=data.skills if data.skills else [],
        schedule_type=data.schedule_type or "flexible",
        work_format=data.work_format or "online",
        github_url=data.github_url or "",
        portfolio_url=data.portfolio_url or "",
        linkedin_url=data.linkedin_url or "",
        style=data.style or "modern",
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return await _serialize_resume(resume, db)


@router.put("/resumes/{resume_id}/")
async def update_resume(
    resume_id: int,
    data: ResumeCreateSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can update resumes")

    profile = await _get_student_profile(user, db)

    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.student_id != profile.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this resume")

    resume.title = data.title
    resume.about = data.about or ""
    resume.skills = data.skills if data.skills else []
    resume.schedule_type = data.schedule_type or "flexible"
    resume.work_format = data.work_format or "online"
    resume.github_url = data.github_url or ""
    resume.portfolio_url = data.portfolio_url or ""
    resume.linkedin_url = data.linkedin_url or ""
    resume.style = data.style or "modern"

    await db.commit()
    await db.refresh(resume)
    return await _serialize_resume(resume, db)


@router.delete("/resumes/{resume_id}/")
async def delete_resume(
    resume_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can delete resumes")

    profile = await _get_student_profile(user, db)

    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.student_id != profile.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this resume")

    await db.delete(resume)
    await db.commit()
    return {"detail": "Resume deleted"}


# ──────────────────────────── JOBS ────────────────────────────


@router.get("/jobs/mine/")
async def list_my_jobs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "employer":
        raise HTTPException(status_code=403, detail="Only employers can view their jobs")

    profile = await _get_employer_profile(user, db)

    app_count = (
        select(Application.job_id, func.count(Application.id).label("cnt"))
        .group_by(Application.job_id)
        .subquery()
    )

    result = await db.execute(
        select(Job, func.coalesce(app_count.c.cnt, 0).label("applications_count"))
        .outerjoin(app_count, Job.id == app_count.c.job_id)
        .where(Job.employer_id == profile.id)
        .order_by(Job.created_at.desc())
    )
    rows = result.all()
    return [await _serialize_job(job, db, count) for job, count in rows]


@router.get("/jobs/")
async def list_jobs(
    category: Optional[str] = Query(None),
    schedule: Optional[str] = Query(None),
    work_format: Optional[str] = Query(None),
    min_age: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    ordering: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    is_employer = user and user.role == "employer"
    employer_profile_id = None
    if is_employer:
        emp = await db.execute(
            select(EmployerProfile).where(EmployerProfile.user_id == user.id)
        )
        emp_profile = emp.scalar_one_or_none()
        if emp_profile:
            employer_profile_id = emp_profile.id

    if is_employer and employer_profile_id:
        query = select(Job).where(
            (Job.is_active == True) | (Job.employer_id == employer_profile_id)
        )
    else:
        query = select(Job).where(Job.is_active == True)

    if category:
        query = query.join(Category, Job.category_id == Category.id, isouter=True).where(
            Category.slug == category
        )
    if schedule:
        query = query.where(Job.schedule == schedule)
    if work_format:
        query = query.where(Job.work_format == work_format)
    if min_age is not None:
        query = query.where(Job.min_age <= min_age)
    if search:
        query = query.where(
            Job.title.ilike(f"%{search}%") | Job.description.ilike(f"%{search}%")
        )

    app_count = (
        select(Application.job_id, func.count(Application.id).label("cnt"))
        .group_by(Application.job_id)
        .subquery()
    )

    query = query.outerjoin(app_count, Job.id == app_count.c.job_id)

    if ordering == "salary_max":
        query = query.order_by(Job.salary_max.desc().nullslast())
    elif ordering == "salary_min":
        query = query.order_by(Job.salary_min.desc().nullslast())
    elif ordering == "created_at":
        query = query.order_by(Job.created_at.desc())
    else:
        query = query.order_by(Job.created_at.desc())

    count_q = select(func.count()).select_from(
        select(Job).where(query.whereclause if query.whereclause else True).subquery()
    )
    total = (await db.execute(count_q)).scalar() or 0

    page_size = 10
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = result.all()

    return {
        "count": total,
        "page": page,
        "results": [await _serialize_job(job, db, count) for job, count in rows],
    }


@router.get("/jobs/{job_id}/")
async def get_job(
    job_id: int,
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    app_count_result = await db.execute(
        select(func.count(Application.id)).where(Application.job_id == job_id)
    )
    applications_count = app_count_result.scalar() or 0

    return await _serialize_job(job, db, applications_count)


@router.post("/jobs/")
async def create_job(
    data: JobCreateSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "employer":
        raise HTTPException(status_code=403, detail="Only employers can create jobs")

    profile = await _get_employer_profile(user, db)

    job = Job(
        employer_id=profile.id,
        category_id=data.category,
        title=data.title,
        description=data.description or "",
        salary_min=data.salary_min,
        salary_max=data.salary_max,
        min_age=data.min_age or 16,
        schedule=data.schedule or "flexible",
        work_format=data.work_format or "online",
        experience_required=data.experience_required if data.experience_required is not None else False,
        image=data.image or "",
        location_lat=data.location_lat,
        location_lng=data.location_lng,
        location_address=data.location_address or "",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return await _serialize_job(job, db)


@router.put("/jobs/{job_id}/")
async def update_job(
    job_id: int,
    data: JobCreateSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "employer":
        raise HTTPException(status_code=403, detail="Only employers can update jobs")

    profile = await _get_employer_profile(user, db)

    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.employer_id != profile.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this job")

    job.category_id = data.category
    job.title = data.title
    job.description = data.description or ""
    job.salary_min = data.salary_min
    job.salary_max = data.salary_max
    job.min_age = data.min_age or 16
    job.schedule = data.schedule or "flexible"
    job.work_format = data.work_format or "online"
    job.experience_required = data.experience_required if data.experience_required is not None else False
    job.image = data.image or ""
    job.location_lat = data.location_lat
    job.location_lng = data.location_lng
    job.location_address = data.location_address or ""

    await db.commit()
    await db.refresh(job)
    return await _serialize_job(job, db)


@router.delete("/jobs/{job_id}/")
async def delete_job(
    job_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "employer":
        raise HTTPException(status_code=403, detail="Only employers can delete jobs")

    profile = await _get_employer_profile(user, db)

    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.employer_id != profile.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this job")

    await db.delete(job)
    await db.commit()
    return {"detail": "Job deleted"}


@router.post("/jobs/{job_id}/toggle_active/")
async def toggle_active(
    job_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "employer":
        raise HTTPException(status_code=403, detail="Only employers can toggle job status")

    profile = await _get_employer_profile(user, db)

    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.employer_id != profile.id:
        raise HTTPException(status_code=403, detail="Not authorized to toggle this job")

    job.is_active = not job.is_active
    await db.commit()
    await db.refresh(job)
    return {"is_active": job.is_active}


# ──────────────────────────── APPLICATIONS ────────────────────────────


@router.get("/applications/")
async def list_applications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role == "student":
        profile = await _get_student_profile(user, db)
        result = await db.execute(
            select(Application).where(
                Application.resume_id.in_(
                    select(Resume.id).where(Resume.student_id == profile.id)
                )
            )
        )
    elif user.role == "employer":
        profile = await _get_employer_profile(user, db)
        result = await db.execute(
            select(Application).where(
                Application.job_id.in_(
                    select(Job.id).where(Job.employer_id == profile.id)
                )
            )
        )
    else:
        return []

    apps = result.scalars().all()
    return [await _serialize_application(a, db) for a in apps]


@router.get("/applications/{application_id}/")
async def get_application(
    application_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application).where(Application.id == application_id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if user.role == "student":
        profile = await _get_student_profile(user, db)
        resume_check = await db.execute(
            select(Resume.id).where(
                Resume.id == app.resume_id, Resume.student_id == profile.id
            )
        )
        if not resume_check.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Not authorized")
    elif user.role == "employer":
        profile = await _get_employer_profile(user, db)
        job_check = await db.execute(
            select(Job.id).where(
                Job.id == app.job_id, Job.employer_id == profile.id
            )
        )
        if not job_check.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Not authorized")

    return await _serialize_application(app, db)


@router.post("/applications/")
async def create_application(
    data: ApplicationCreateSchema,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can apply")

    profile = await _get_student_profile(user, db)

    resume_result = await db.execute(
        select(Resume).where(Resume.id == data.resume, Resume.student_id == profile.id)
    )
    resume = resume_result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found or not yours")

    job_result = await db.execute(select(Job).where(Job.id == data.job))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    existing = await db.execute(
        select(Application).where(
            Application.job_id == data.job, Application.resume_id == data.resume
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You have already applied to this job with this resume")

    app = Application(
        job_id=data.job,
        resume_id=data.resume,
        cover_letter=data.cover_letter or "",
        status="sent",
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return await _serialize_application(app, db)


@router.post("/applications/{application_id}/update_status/")
async def update_application_status(
    application_id: int,
    data: ApplicationStatusUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "employer":
        raise HTTPException(status_code=403, detail="Only employers can update application status")

    profile = await _get_employer_profile(user, db)

    result = await db.execute(
        select(Application).where(Application.id == application_id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    job_result = await db.execute(
        select(Job).where(Job.id == app.job_id, Job.employer_id == profile.id)
    )
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=403, detail="Not authorized to update this application")

    valid_statuses = ["sent", "reviewed", "interview", "accepted", "rejected"]
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    app.status = data.status
    await db.commit()
    await db.refresh(app)

    resume_result = await db.execute(
        select(Resume).where(Resume.id == app.resume_id)
    )
    resume = resume_result.scalar_one_or_none()
    if resume:
        student_result = await db.execute(
            select(StudentProfile).where(StudentProfile.id == resume.student_id)
        )
        student = student_result.scalar_one_or_none()
        if student:
            employer_user_result = await db.execute(
                select(User).where(User.id == profile.user_id)
            )
            employer_user = employer_user_result.scalar_one_or_none()
            company_name = profile.company_name
            status_display = data.status.replace("_", " ").title()

            notification = Notification(
                user_id=student.user_id,
                notification_type="application_update",
                title=f"Application update: {job.title}",
                message=f"{company_name} updated your application status to '{status_display}'",
                link=f"/applications/{app.id}",
            )
            db.add(notification)
            await db.commit()

            try:
                from main import app as fastapi_app
                ws_manager = getattr(fastapi_app.state, "ws_manager", None)
                if ws_manager:
                    await ws_manager.send_to_user(
                        student.user_id,
                        {
                            "type": "notification",
                            "data": {
                                "id": notification.id,
                                "notification_type": notification.notification_type,
                                "title": notification.title,
                                "message": notification.message,
                                "link": notification.link,
                                "is_read": False,
                                "created_at": notification.created_at.isoformat() if notification.created_at else None,
                            },
                        },
                    )
            except Exception:
                pass

    return await _serialize_application(app, db)
