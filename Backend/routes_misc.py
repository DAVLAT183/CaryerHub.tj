from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from database import get_db
from models import (
    Favorite, Job, Notification, ChatSession, ChatMessage,
    DirectMessage, User, StudentProfile, EmployerProfile, Application,
    Resume,
)
from schemas import (
    FavoriteCreate, FavoriteResponse, NotificationResponse,
    ChatSessionCreate, ChatSessionResponse, ChatMessageCreate,
    ChatMessageResponse, DirectMessageCreate, DirectMessageResponse,
    ConversationResponse, UserResponse,
)
from auth import get_current_user, get_optional_user

router = APIRouter(prefix="/api", tags=["Misc"])


# ──────────────────────────────────────────────
# FAVORITES
# ──────────────────────────────────────────────

@router.get("/favorites/", response_model=list[FavoriteResponse])
async def list_favorites(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student_profile = (await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )).scalar_one_or_none()

    if not student_profile:
        raise HTTPException(status_code=400, detail="Student profile not found")

    result = await db.execute(
        select(Favorite)
        .where(Favorite.student_id == student_profile.id)
        .order_by(desc(Favorite.created_at))
    )
    favorites = result.scalars().all()

    responses = []
    for fav in favorites:
        resp = FavoriteResponse(
            id=fav.id,
            student_id=fav.student_id,
            job_id=fav.job_id,
            created_at=fav.created_at,
        )
        job = (await db.execute(
            select(Job).where(Job.id == fav.job_id)
        )).scalar_one_or_none()
        if job:
            resp.job_title = job.title
            employer = (await db.execute(
                select(EmployerProfile).where(EmployerProfile.id == job.employer_id)
            )).scalar_one_or_none()
            resp.company_name = employer.company_name if employer else None
        responses.append(resp)
    return responses


@router.post("/favorites/add/", response_model=FavoriteResponse, status_code=201)
async def add_favorite(
    favorite_in: FavoriteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student_profile = (await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )).scalar_one_or_none()

    if not student_profile:
        raise HTTPException(status_code=400, detail="Student profile not found")

    job = (await db.execute(
        select(Job).where(Job.id == favorite_in.job_id)
    )).scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    existing = (await db.execute(
        select(Favorite).where(
            and_(
                Favorite.student_id == student_profile.id,
                Favorite.job_id == favorite_in.job_id,
            )
        )
    )).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Job already in favorites")

    favorite = Favorite(student_id=student_profile.id, job_id=favorite_in.job_id)
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)

    resp = FavoriteResponse(
        id=favorite.id,
        student_id=favorite.student_id,
        job_id=favorite.job_id,
        created_at=favorite.created_at,
        job_title=job.title,
    )
    employer = (await db.execute(
        select(EmployerProfile).where(EmployerProfile.id == job.employer_id)
    )).scalar_one_or_none()
    resp.company_name = employer.company_name if employer else None
    return resp


@router.delete("/favorites/{job_id}/remove/", status_code=204)
async def remove_favorite(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student_profile = (await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )).scalar_one_or_none()

    if not student_profile:
        raise HTTPException(status_code=400, detail="Student profile not found")

    favorite = (await db.execute(
        select(Favorite).where(
            and_(
                Favorite.student_id == student_profile.id,
                Favorite.job_id == job_id,
            )
        )
    )).scalar_one_or_none()

    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")

    await db.delete(favorite)
    await db.commit()


@router.post("/favorites/", response_model=FavoriteResponse, status_code=201)
async def create_favorite(
    favorite_in: FavoriteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await add_favorite(favorite_in, db, current_user)


# ──────────────────────────────────────────────
# NOTIFICATIONS
# ──────────────────────────────────────────────

@router.get("/notifications/", response_model=list[NotificationResponse])
async def list_notifications(
    is_read: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Notification).where(Notification.user_id == current_user.id)

    if is_read is not None:
        stmt = stmt.where(Notification.is_read == is_read)

    result = await db.execute(stmt.order_by(desc(Notification.created_at)))
    return result.scalars().all()


@router.get("/notifications/unread_count/")
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(func.count(Notification.id)).where(
            and_(
                Notification.user_id == current_user.id,
                Notification.is_read == False,
            )
        )
    )
    count = result.scalar()
    return {"unread_count": count}


@router.post("/notifications/mark_all_read/", status_code=200)
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification).where(
            and_(
                Notification.user_id == current_user.id,
                Notification.is_read == False,
            )
        )
    )
    notifications = result.scalars().all()
    for notif in notifications:
        notif.is_read = True
    await db.commit()
    return {"detail": f"Marked {len(notifications)} notifications as read"}


@router.post("/notifications/{notif_id}/mark_read/", response_model=NotificationResponse)
async def mark_one_read(
    notif_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = (await db.execute(
        select(Notification).where(
            and_(
                Notification.id == notif_id,
                Notification.user_id == current_user.id,
            )
        )
    )).scalar_one_or_none()

    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.is_read = True
    await db.commit()
    await db.refresh(notif)
    return notif


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None


@router.patch("/notifications/{notif_id}/", response_model=NotificationResponse)
async def update_notification(
    notif_id: int,
    payload: NotificationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = (await db.execute(
        select(Notification).where(
            and_(
                Notification.id == notif_id,
                Notification.user_id == current_user.id,
            )
        )
    )).scalar_one_or_none()

    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    if payload.is_read is not None:
        notif.is_read = payload.is_read

    await db.commit()
    await db.refresh(notif)
    return notif


@router.delete("/notifications/{notif_id}", status_code=204)
async def delete_notification(
    notif_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = (await db.execute(
        select(Notification).where(
            and_(
                Notification.id == notif_id,
                Notification.user_id == current_user.id,
            )
        )
    )).scalar_one_or_none()

    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    await db.delete(notif)
    await db.commit()


# ──────────────────────────────────────────────
# CHAT SESSIONS
# ──────────────────────────────────────────────

@router.get("/chat/sessions/", response_model=list[ChatSessionResponse])
async def list_chat_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(desc(ChatSession.updated_at))
    )
    sessions = result.scalars().all()

    responses = []
    for sess in sessions:
        resp = ChatSessionResponse.model_validate(sess)

        last_msg_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == sess.id)
            .order_by(desc(ChatMessage.created_at))
            .limit(1)
        )
        last_msg = last_msg_result.scalar_one_or_none()
        resp.last_message = last_msg.content if last_msg else None

        msg_count_result = await db.execute(
            select(func.count(ChatMessage.id)).where(ChatMessage.session_id == sess.id)
        )
        resp.messages_count = msg_count_result.scalar()

        responses.append(resp)
    return responses


@router.get("/chat/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (await db.execute(
        select(ChatSession).where(
            and_(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.id,
            )
        )
    )).scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    resp = ChatSessionResponse.model_validate(session)

    messages_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at)
    )
    resp.messages = [ChatMessageResponse.model_validate(m) for m in messages_result.scalars().all()]
    resp.messages_count = len(resp.messages)

    last = resp.messages[-1] if resp.messages else None
    resp.last_message = last.content if last else None

    return resp


@router.post("/chat/sessions/", response_model=ChatSessionResponse, status_code=201)
async def create_chat_session(
    session_in: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = ChatSession(
        user_id=current_user.id,
        title=session_in.title or "New Chat",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    resp = ChatSessionResponse.model_validate(session)
    resp.messages = []
    resp.messages_count = 0
    resp.last_message = None
    return resp


@router.put("/chat/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_chat_session(
    session_id: int,
    session_in: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (await db.execute(
        select(ChatSession).where(
            and_(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.id,
            )
        )
    )).scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    if session_in.title is not None:
        session.title = session_in.title

    await db.commit()
    await db.refresh(session)

    resp = ChatSessionResponse.model_validate(session)
    resp.messages = []
    resp.messages_count = 0
    resp.last_message = None
    return resp


@router.delete("/chat/sessions/{session_id}", status_code=204)
async def delete_chat_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (await db.execute(
        select(ChatSession).where(
            and_(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.id,
            )
        )
    )).scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = (await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session.id)
    )).scalars().all()
    for msg in messages:
        await db.delete(msg)

    await db.delete(session)
    await db.commit()


# ──────────────────────────────────────────────
# CHAT MESSAGES
# ──────────────────────────────────────────────

@router.post("/chat/send/", response_model=ChatMessageResponse, status_code=201)
async def send_chat_message(
    message_in: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = None
    if message_in.session_id:
        session = (await db.execute(
            select(ChatSession).where(
                and_(
                    ChatSession.id == message_in.session_id,
                    ChatSession.user_id == current_user.id,
                )
            )
        )).scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
    else:
        session = ChatSession(
            user_id=current_user.id,
            title=message_in.content[:50] if message_in.content else "New Chat",
        )
        db.add(session)
        await db.flush()

    user_message = ChatMessage(
        session_id=session.id,
        role="user",
        content=message_in.content,
    )
    db.add(user_message)
    await db.flush()

    try:
        from ai_service import _chat_with_gemini
        history_msgs = (await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at)
        )).scalars().all()

        messages_for_ai = [{"role": m.role, "content": m.content} for m in history_msgs]
        ai_response_text = await _chat_with_gemini(messages_for_ai)
    except Exception:
        lower = message_in.content.lower()
        if any(w in lower for w in ["hello", "hi", "hey", "привет"]):
            ai_response_text = "Hello! I'm your AI career consultant. How can I help you today?"
        elif "salary" in lower or "зарплат" in lower:
            ai_response_text = "Salary expectations vary by role, industry, and experience. Research market rates on sites like Glassdoor or Payscale."
        elif "resume" in lower or "резюме" in lower:
            ai_response_text = "A strong resume highlights quantifiable achievements, uses action verbs, and is tailored to the job description."
        elif "interview" in lower or "собеседован" in lower:
            ai_response_text = "Practice common questions, research the company, and prepare thoughtful questions to ask the interviewer."
        else:
            ai_response_text = "I'm here to help with your career questions. Feel free to ask about jobs, resumes, interviews, or career growth."

    ai_message = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=ai_response_text,
    )
    db.add(ai_message)

    from datetime import datetime, timezone
    session.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(ai_message)

    resp = ChatMessageResponse.model_validate(ai_message)
    resp.session_id = session.id
    return resp


@router.get("/chat/{session_id}/messages/", response_model=list[ChatMessageResponse])
async def get_session_messages(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (await db.execute(
        select(ChatSession).where(
            and_(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.id,
            )
        )
    )).scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()

    return [
        ChatMessageResponse.model_validate(m) for m in messages
    ]


# ──────────────────────────────────────────────
# DIRECT MESSAGES
# ──────────────────────────────────────────────

@router.get("/messages/conversations/", response_model=list[ConversationResponse])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sent_subq = (
        select(
            DirectMessage.recipient_id.label("other_id"),
            DirectMessage.created_at,
        )
        .where(DirectMessage.sender_id == current_user.id)
        .subquery()
    )

    received_subq = (
        select(
            DirectMessage.sender_id.label("other_id"),
            DirectMessage.created_at,
        )
        .where(DirectMessage.recipient_id == current_user.id)
        .subquery()
    )

    all_msgs = sent_subq.union_all(received_subq).subquery()

    latest = (
        select(
            all_msgs.c.other_id,
            func.max(all_msgs.c.created_at).label("last_message_at"),
        )
        .group_by(all_msgs.c.other_id)
        .order_by(desc("last_message_at"))
    )

    result = await db.execute(latest)
    rows = result.all()

    conversations = []
    for row in rows:
        other_user = (await db.execute(
            select(User).where(User.id == row.other_id)
        )).scalar_one_or_none()

        if not other_user:
            continue

        unread_result = await db.execute(
            select(func.count(DirectMessage.id)).where(
                and_(
                    DirectMessage.sender_id == row.other_id,
                    DirectMessage.recipient_id == current_user.id,
                    DirectMessage.is_read == False,
                )
            )
        )
        unread_count = unread_result.scalar()

        last_msg_result = await db.execute(
            select(DirectMessage).where(
                or_(
                    and_(
                        DirectMessage.sender_id == current_user.id,
                        DirectMessage.recipient_id == row.other_id,
                    ),
                    and_(
                        DirectMessage.sender_id == row.other_id,
                        DirectMessage.recipient_id == current_user.id,
                    ),
                )
            )
            .order_by(desc(DirectMessage.created_at))
            .limit(1)
        )
        last_msg = last_msg_result.scalar_one_or_none()

        conv = ConversationResponse(
            user=UserResponse.model_validate(other_user),
            last_message=DirectMessageResponse.model_validate(last_msg) if last_msg else None,
            unread_count=unread_count,
            last_message_at=row.last_message_at,
        )
        conversations.append(conv)

    return conversations


@router.get("/messages/{user_id}/", response_model=list[DirectMessageResponse])
async def get_messages_with_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot message yourself")

    other_user = (await db.execute(
        select(User).where(User.id == user_id)
    )).scalar_one_or_none()

    if not other_user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(DirectMessage).where(
            or_(
                and_(
                    DirectMessage.sender_id == current_user.id,
                    DirectMessage.recipient_id == user_id,
                ),
                and_(
                    DirectMessage.sender_id == user_id,
                    DirectMessage.recipient_id == current_user.id,
                ),
            )
        ).order_by(DirectMessage.created_at)
    )
    messages = result.scalars().all()

    unread_to_mark = [
        m for m in messages
        if m.sender_id == user_id and m.recipient_id == current_user.id and not m.is_read
    ]
    for msg in unread_to_mark:
        msg.is_read = True

    if unread_to_mark:
        await db.commit()

    return [DirectMessageResponse.model_validate(m) for m in messages]


@router.post("/messages/{user_id}/", response_model=DirectMessageResponse, status_code=201)
async def send_direct_message(
    user_id: int,
    message_in: DirectMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot message yourself")

    other_user = (await db.execute(
        select(User).where(User.id == user_id)
    )).scalar_one_or_none()

    if not other_user:
        raise HTTPException(status_code=404, detail="User not found")

    dm = DirectMessage(
        sender_id=current_user.id,
        recipient_id=user_id,
        content=message_in.content,
    )
    db.add(dm)

    sender_name = current_user.first_name or current_user.username
    notification = Notification(
        user_id=user_id,
        notification_type="message",
        title="New Message",
        message=f"You have a new message from {sender_name}",
    )
    db.add(notification)

    await db.commit()
    await db.refresh(dm)

    return DirectMessageResponse.model_validate(dm)


@router.get("/messages/employers/", response_model=list[UserResponse])
async def list_employers_for_chat(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student_profile = (await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )).scalar_one_or_none()

    if not student_profile:
        raise HTTPException(status_code=400, detail="Student profile not found")

    applications_result = await db.execute(
        select(Application)
        .join(Resume, Application.resume_id == Resume.id)
        .where(Resume.student_id == student_profile.id)
    )
    applications = applications_result.scalars().all()

    if not applications:
        return []

    employer_ids = set()
    for app in applications:
        job_result = await db.execute(select(Job).where(Job.id == app.job_id))
        job = job_result.scalar_one_or_none()
        if job:
            emp_result = await db.execute(
                select(EmployerProfile).where(EmployerProfile.id == job.employer_id)
            )
            emp = emp_result.scalar_one_or_none()
            if emp:
                employer_ids.add(emp.user_id)

    if not employer_ids:
        return []

    employers_result = await db.execute(
        select(User).where(User.id.in_(employer_ids))
    )

    return [UserResponse.model_validate(u) for u in employers_result.scalars().all()]
