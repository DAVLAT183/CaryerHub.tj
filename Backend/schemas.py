from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ──────────────────────────── Auth ────────────────────────────


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str
    phone: Optional[str] = None
    company_name: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh: str


# ──────────────────────────── User ────────────────────────────


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    phone: Optional[str] = None
    avatar: Optional[str] = None
    location: Optional[str] = None
    student_profile_id: Optional[int] = None
    employer_profile_id: Optional[int] = None


class UserRegisterSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    password: Optional[str] = Field(None, exclude=True)
    role: str
    phone: Optional[str] = None
    location: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    phone: Optional[str] = None
    avatar: Optional[str] = None
    location: Optional[str] = None
    is_email_verified: bool = False
    current_plan: Optional[str] = None


class TokenResponse(BaseModel):
    access: str
    refresh: str
    user: UserResponse


# ──────────────────────────── Profiles ────────────────────────────


class StudentProfileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user: UserSchema
    university: Optional[str] = None
    faculty: Optional[str] = None
    course: Optional[int] = None
    birth_date: Optional[date] = None
    age: Optional[int] = None
    city: Optional[str] = None


class EmployerProfileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user: UserSchema
    company_name: str
    description: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    is_verified: bool = False


# ──────────────────────────── Lookups ────────────────────────────


class CategorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class CategoryWithCountSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    jobs_count: int = 0


class WorkScheduleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class WorkFormatSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class WorkExperienceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


# ──────────────────────────── Resume ────────────────────────────


class ResumeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student: StudentProfileSchema
    title: str
    about: Optional[str] = None
    skills: Optional[str] = None
    schedule_type: Optional[str] = None
    work_format: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    style: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ResumeCreateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    about: Optional[str] = None
    skills: Optional[str] = None
    schedule_type: Optional[str] = None
    work_format: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    style: Optional[str] = None


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    about: Optional[str] = None
    skills: Optional[str] = None
    schedule_type: Optional[str] = None
    work_format: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    style: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ──────────────────────────── Job ────────────────────────────


class JobSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employer: EmployerProfileSchema
    category: Optional[CategorySchema] = None
    category_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    min_age: Optional[int] = None
    schedule: Optional[str] = None
    work_format: Optional[str] = None
    experience_required: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    applications_count: int = 0
    is_favorited: bool = False
    image: Optional[str] = None
    image_url: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    location_address: Optional[str] = None
    has_location: bool = False
    source: Optional[str] = None
    source_url: Optional[str] = None
    source_id: Optional[str] = None


class JobCreateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: Optional[int] = None
    title: str
    description: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    min_age: Optional[int] = None
    schedule: Optional[str] = None
    work_format: Optional[str] = None
    experience_required: Optional[str] = None
    image: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    location_address: Optional[str] = None


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    category: Optional[CategorySchema] = None
    category_name: Optional[str] = None
    schedule: Optional[str] = None
    work_format: Optional[str] = None
    experience_required: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    applications_count: int = 0
    image: Optional[str] = None
    image_url: Optional[str] = None
    location_address: Optional[str] = None
    employer: Optional[EmployerProfileSchema] = None


# ──────────────────────────── Application ────────────────────────────


class ApplicationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job: Optional[JobSchema] = None
    job_title: Optional[str] = None
    job_employer_name: Optional[str] = None
    resume: Optional[ResumeSchema] = None
    student_name: Optional[str] = None
    status: str = "pending"
    cover_letter: Optional[str] = None
    created_at: Optional[datetime] = None


class ApplicationCreateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job: int
    resume: int
    cover_letter: Optional[str] = None


# ──────────────────────────── Favorite ────────────────────────────


class FavoriteSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job: Optional[JobSchema] = None
    job_id: Optional[int] = None
    created_at: Optional[datetime] = None


# ──────────────────────────── Chat / AI ────────────────────────────


class ChatMessageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    created_at: Optional[datetime] = None


class ChatSessionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: Optional[str] = None
    messages: list[ChatMessageSchema] = []
    last_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ChatSessionListSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: Optional[str] = None
    last_message: Optional[str] = None
    messages_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ──────────────────────────── Direct Messages ────────────────────────────


class DirectMessageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender: Optional[int] = None
    sender_name: Optional[str] = None
    recipient: Optional[int] = None
    recipient_name: Optional[str] = None
    content: str
    created_at: Optional[datetime] = None
    is_read: bool = False


# ──────────────────────────── Notifications ────────────────────────────


class NotificationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    notification_type: Optional[str] = None
    title: str
    message: Optional[str] = None
    link: Optional[str] = None
    is_read: bool = False
    created_at: Optional[datetime] = None
    employer_avatar: Optional[str] = None


# ──────────────────────────── Subscriptions / Payments ────────────────────────────


class TariffPlanSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    display_name: str
    price: int
    duration_days: int
    features: Optional[Any] = None


class UserSubscriptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan: Optional[TariffPlanSchema] = None
    status: str = "active"
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class PaymentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_no: Optional[str] = None
    amount: int
    status: str = "pending"
    payment_method: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    subscription_plan: Optional[TariffPlanSchema] = None


class CreatePaymentSchema(BaseModel):
    plan_id: int


# ──────────────────────────── User Update ────────────────────────────


class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    location: Optional[str] = None


# ──────────────────────────── Profile Create/Update ────────────────────────────


class StudentProfileCreate(BaseModel):
    university: Optional[str] = None
    faculty: Optional[str] = None
    course: Optional[int] = None
    birth_date: Optional[str] = None
    age: Optional[int] = None
    city: Optional[str] = None


class StudentProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    university: Optional[str] = None
    faculty: Optional[str] = None
    course: Optional[int] = None
    birth_date: Optional[str] = None
    age: Optional[int] = None
    city: Optional[str] = None


class EmployerProfileCreate(BaseModel):
    company_name: str
    description: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None


class EmployerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    company_name: str
    description: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    is_verified: bool = False


# ──────────────────────────── Category ────────────────────────────


class CategoryCreate(BaseModel):
    name: str
    slug: str


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


# ──────────────────────────── Work Lookups ────────────────────────────


class WorkScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class WorkFormatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class WorkExperienceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


# ──────────────────────────── Favorite ────────────────────────────


class FavoriteCreate(BaseModel):
    job_id: int


class FavoriteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: Optional[int] = None
    job_id: Optional[int] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    created_at: Optional[datetime] = None


# ──────────────────────────── Notification ────────────────────────────


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    notification_type: Optional[str] = None
    title: str
    message: Optional[str] = None
    link: Optional[str] = None
    is_read: bool = False
    created_at: Optional[datetime] = None


# ──────────────────────────── Chat ────────────────────────────


class ChatSessionCreate(BaseModel):
    title: Optional[str] = None


class ChatMessageCreate(BaseModel):
    session_id: Optional[int] = None
    content: str


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: Optional[int] = None
    role: str
    content: str
    created_at: Optional[datetime] = None


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: Optional[str] = None
    messages: list[ChatMessageResponse] = []
    messages_count: int = 0
    last_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ──────────────────────────── Direct Messages ────────────────────────────


class DirectMessageCreate(BaseModel):
    content: str


class DirectMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender_id: Optional[int] = None
    recipient_id: Optional[int] = None
    content: str
    created_at: Optional[datetime] = None
    is_read: bool = False


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user: Optional[UserResponse] = None
    last_message: Optional[DirectMessageResponse] = None
    unread_count: int = 0
    last_message_at: Optional[datetime] = None
