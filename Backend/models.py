import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, JSON, Float, Enum as SAEnum,
)
from sqlalchemy.orm import relationship
from database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, index=True, nullable=False)
    email = Column(String(254), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=True)
    first_name = Column(String(150), default="")
    last_name = Column(String(150), default="")
    role = Column(String(10), default="student")
    phone = Column(String(20), default="")
    avatar = Column(String(500), default="")
    location = Column(String(200), default="")
    is_email_verified = Column(Boolean, default=False)
    current_plan = Column(String(20), default="free")
    is_active = Column(Boolean, default=True)
    is_staff = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    student_profile = relationship("StudentProfile", back_populates="user", uselist=False)
    employer_profile = relationship("EmployerProfile", back_populates="user", uselist=False)
    notifications = relationship("Notification", back_populates="user")
    subscriptions = relationship("UserSubscription", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    email_verifications = relationship("EmailVerification", back_populates="user")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user")
    sent_messages = relationship("DirectMessage", foreign_keys="DirectMessage.sender_id", back_populates="sender")
    received_messages = relationship("DirectMessage", foreign_keys="DirectMessage.recipient_id", back_populates="recipient")


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    university = Column(String(200), default="")
    faculty = Column(String(200), default="")
    course = Column(Integer, nullable=True)
    birth_date = Column(String(10), nullable=True)
    age = Column(Integer, nullable=True)
    city = Column(String(100), default="")

    user = relationship("User", back_populates="student_profile")
    resumes = relationship("Resume", back_populates="student")
    favorites = relationship("Favorite", back_populates="student")


class EmployerProfile(Base):
    __tablename__ = "employer_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    company_name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    website = Column(String(500), default="")
    address = Column(String(300), default="")
    is_verified = Column(Boolean, default=False)

    user = relationship("User", back_populates="employer_profile")
    jobs = relationship("Job", back_populates="employer")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)

    jobs = relationship("Job", back_populates="category")


class WorkSchedule(Base):
    __tablename__ = "work_schedules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)


class WorkFormat(Base):
    __tablename__ = "work_formats"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)


class WorkExperience(Base):
    __tablename__ = "work_experiences"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    title = Column(String(200), nullable=False)
    about = Column(Text, default="")
    skills = Column(JSON, default=list)
    schedule_type = Column(String(20), default="flexible")
    work_format = Column(String(20), default="online")
    github_url = Column(String(300), default="")
    portfolio_url = Column(String(300), default="")
    linkedin_url = Column(String(300), default="")
    style = Column(String(20), default="modern")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    student = relationship("StudentProfile", back_populates="resumes")
    applications = relationship("Application", back_populates="resume")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    employer_id = Column(Integer, ForeignKey("employer_profiles.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    min_age = Column(Integer, default=16)
    schedule = Column(String(20), default="flexible")
    work_format = Column(String(20), default="online")
    experience_required = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    image = Column(String(500), default="")
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    location_address = Column(String(300), default="")
    source = Column(String(20), default="manual")
    source_url = Column(String(500), default="")
    source_id = Column(String(100), default="")
    created_at = Column(DateTime, default=utcnow)

    employer = relationship("EmployerProfile", back_populates="jobs")
    category = relationship("Category", back_populates="jobs")
    applications = relationship("Application", back_populates="job")
    favorited_by = relationship("Favorite", back_populates="job")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    status = Column(String(20), default="sent")
    cover_letter = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow)

    job = relationship("Job", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    created_at = Column(DateTime, default=utcnow)

    student = relationship("StudentProfile", back_populates="favorites")
    job = relationship("Job", back_populates="favorited_by")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_type = Column(String(30), default="system")
    title = Column(String(200), nullable=False)
    message = Column(Text, default="")
    link = Column(String(300), default="")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="notifications")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(200), default="Новый чат")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    messages = relationship("ChatMessage", back_populates="session", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(10), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    session = relationship("ChatSession", back_populates="messages")


class DirectMessage(Base):
    __tablename__ = "direct_messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    is_read = Column(Boolean, default=False)

    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_messages")


class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    is_used = Column(Boolean, default=False)

    user = relationship("User", back_populates="email_verifications")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    is_used = Column(Boolean, default=False)

    user = relationship("User", back_populates="password_reset_tokens")


class TariffPlan(Base):
    __tablename__ = "tariff_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    price = Column(Integer, default=0)
    duration_days = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    features = Column(JSON, default=list)
    created_at = Column(DateTime, default=utcnow)

    subscriptions = relationship("UserSubscription", back_populates="plan")


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("tariff_plans.id"), nullable=False)
    status = Column(String(20), default="pending")
    started_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="subscriptions")
    plan = relationship("TariffPlan", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("user_subscriptions.id"), nullable=False)
    invoice_no = Column(String(100), unique=True, nullable=False)
    amount = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")
    payment_method = Column(String(50), default="")
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="payments")
    subscription = relationship("UserSubscription", back_populates="payments")
