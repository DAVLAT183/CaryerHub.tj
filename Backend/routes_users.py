from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import re as _re
from database import get_db
from models import (
    User,
    StudentProfile,
    EmployerProfile,
    Category,
    WorkSchedule,
    WorkFormat,
    WorkExperience,
    DirectMessage,
    Job,
)
from schemas import (
    UserResponse,
    UserUpdateRequest,
    StudentProfileResponse,
    StudentProfileCreate,
    EmployerProfileResponse,
    EmployerProfileCreate,
    CategoryResponse,
    CategoryCreate,
)
from auth import get_current_user


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = _re.sub(r'[^\w\s-]', '', text)
    text = _re.sub(r'[\s_]+', '-', text)
    return text.strip('-')

router = APIRouter(tags=["Profiles"])


@router.get("/users/", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.is_staff:
        result = await db.execute(select(User))
        return result.scalars().all()

    partner_ids = set()
    dms = await db.execute(
        select(DirectMessage).where(
            (DirectMessage.sender_id == current_user.id)
            | (DirectMessage.recipient_id == current_user.id)
        )
    )
    for dm in dms.scalars().all():
        if dm.sender_id != current_user.id:
            partner_ids.add(dm.sender_id)
        if dm.recipient_id != current_user.id:
            partner_ids.add(dm.recipient_id)

    if not partner_ids:
        return []

    result = await db.execute(select(User).where(User.id.in_(partner_ids)))
    return result.scalars().all()


@router.get("/users/me/", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.patch("/users/me/", response_model=UserResponse)
async def update_current_user_profile(
    update_data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.get("/student-profiles/", response_model=List[StudentProfileResponse])
async def list_student_profiles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(StudentProfile))
    return result.scalars().all()


@router.get("/student-profiles/{profile_id}", response_model=StudentProfileResponse)
async def get_student_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return profile


@router.post(
    "/student-profiles/",
    response_model=StudentProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_student_profile(
    profile_data: StudentProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail="Student profile already exists for this user"
        )
    profile = StudentProfile(user_id=current_user.id, **profile_data.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.put("/student-profiles/{profile_id}", response_model=StudentProfileResponse)
async def update_student_profile(
    profile_id: int,
    profile_data: StudentProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    if profile.user_id != current_user.id and not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")
    for field, value in profile_data.model_dump().items():
        setattr(profile, field, value)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.delete("/student-profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    if profile.user_id != current_user.id and not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized to delete this profile")
    await db.delete(profile)
    await db.commit()


@router.get("/employer-profiles/", response_model=List[EmployerProfileResponse])
async def list_employer_profiles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(EmployerProfile))
    return result.scalars().all()


@router.get("/employer-profiles/{profile_id}", response_model=EmployerProfileResponse)
async def get_employer_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmployerProfile).where(EmployerProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Employer profile not found")
    return profile


@router.post(
    "/employer-profiles/",
    response_model=EmployerProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_employer_profile(
    profile_data: EmployerProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(EmployerProfile).where(EmployerProfile.user_id == current_user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail="Employer profile already exists for this user"
        )
    profile = EmployerProfile(user_id=current_user.id, **profile_data.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.put("/employer-profiles/{profile_id}", response_model=EmployerProfileResponse)
async def update_employer_profile(
    profile_id: int,
    profile_data: EmployerProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmployerProfile).where(EmployerProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Employer profile not found")
    if profile.user_id != current_user.id and not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")
    for field, value in profile_data.model_dump().items():
        setattr(profile, field, value)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.delete("/employer-profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employer_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmployerProfile).where(EmployerProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Employer profile not found")
    if profile.user_id != current_user.id and not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized to delete this profile")
    await db.delete(profile)
    await db.commit()


@router.get("/categories/", response_model=List[CategoryResponse])
async def list_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Category))
    return result.scalars().all()


@router.get("/categories/{slug}", response_model=CategoryResponse)
async def get_category(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Category).where(Category.slug == slug))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post(
    "/categories/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    existing = await db.execute(
        select(Category).where(Category.slug == category_data.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Category with this slug already exists")
    category = Category(**category_data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.put("/categories/{slug}", response_model=CategoryResponse)
async def update_category(
    slug: str,
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    result = await db.execute(select(Category).where(Category.slug == slug))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    for field, value in category_data.model_dump().items():
        setattr(category, field, value)
    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/categories/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    result = await db.execute(select(Category).where(Category.slug == slug))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.delete(category)
    await db.commit()


@router.get("/work-schedules/")
async def list_work_schedules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WorkSchedule))
    items = result.scalars().all()
    return [{"id": w.id, "name": w.name, "slug": w.slug} for w in items]


@router.post(
    "/work-schedules/",
    status_code=status.HTTP_201_CREATED,
)
async def create_work_schedule(
    name: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    slug = _slugify(name)
    ws = WorkSchedule(name=name, slug=slug)
    db.add(ws)
    await db.commit()
    await db.refresh(ws)
    return {"id": ws.id, "name": ws.name, "slug": ws.slug}


@router.put("/work-schedules/{ws_id}")
async def update_work_schedule(
    ws_id: int,
    name: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    result = await db.execute(select(WorkSchedule).where(WorkSchedule.id == ws_id))
    ws = result.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Work schedule not found")
    ws.name = name
    ws.slug = _slugify(name)
    await db.commit()
    await db.refresh(ws)
    return {"id": ws.id, "name": ws.name, "slug": ws.slug}


@router.delete("/work-schedules/{ws_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_schedule(
    ws_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    result = await db.execute(select(WorkSchedule).where(WorkSchedule.id == ws_id))
    ws = result.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Work schedule not found")
    await db.delete(ws)
    await db.commit()


@router.get("/work-formats/")
async def list_work_formats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WorkFormat))
    items = result.scalars().all()
    return [{"id": w.id, "name": w.name, "slug": w.slug} for w in items]


@router.post(
    "/work-formats/",
    status_code=status.HTTP_201_CREATED,
)
async def create_work_format(
    name: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    slug = _slugify(name)
    wf = WorkFormat(name=name, slug=slug)
    db.add(wf)
    await db.commit()
    await db.refresh(wf)
    return {"id": wf.id, "name": wf.name, "slug": wf.slug}


@router.put("/work-formats/{wf_id}")
async def update_work_format(
    wf_id: int,
    name: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    result = await db.execute(select(WorkFormat).where(WorkFormat.id == wf_id))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Work format not found")
    wf.name = name
    wf.slug = _slugify(name)
    await db.commit()
    await db.refresh(wf)
    return {"id": wf.id, "name": wf.name, "slug": wf.slug}


@router.delete("/work-formats/{wf_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_format(
    wf_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    result = await db.execute(select(WorkFormat).where(WorkFormat.id == wf_id))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Work format not found")
    await db.delete(wf)
    await db.commit()


@router.get("/work-experiences/")
async def list_work_experiences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WorkExperience))
    items = result.scalars().all()
    return [{"id": w.id, "name": w.name, "slug": w.slug} for w in items]


@router.post(
    "/work-experiences/",
    status_code=status.HTTP_201_CREATED,
)
async def create_work_experience(
    name: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    slug = _slugify(name)
    we = WorkExperience(name=name, slug=slug)
    db.add(we)
    await db.commit()
    await db.refresh(we)
    return {"id": we.id, "name": we.name, "slug": we.slug}


@router.put("/work-experiences/{we_id}")
async def update_work_experience(
    we_id: int,
    name: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    result = await db.execute(select(WorkExperience).where(WorkExperience.id == we_id))
    we = result.scalar_one_or_none()
    if not we:
        raise HTTPException(status_code=404, detail="Work experience not found")
    we.name = name
    we.slug = _slugify(name)
    await db.commit()
    await db.refresh(we)
    return {"id": we.id, "name": we.name, "slug": we.slug}


@router.delete("/work-experiences/{we_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_experience(
    we_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Admin only")
    result = await db.execute(select(WorkExperience).where(WorkExperience.id == we_id))
    we = result.scalar_one_or_none()
    if not we:
        raise HTTPException(status_code=404, detail="Work experience not found")
    await db.delete(we)
    await db.commit()
