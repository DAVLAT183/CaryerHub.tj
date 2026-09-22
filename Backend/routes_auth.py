from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from database import get_db
from models import User, StudentProfile, EmployerProfile
from schemas import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, UserResponse
from auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, get_current_user,
)
from config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register/", response_model=TokenResponse)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where((User.username == data.username) | (User.email == data.email)))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username or email already exists")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=data.role,
        phone=data.phone,
        first_name=data.username,
    )
    db.add(user)
    await db.flush()

    if data.role == "student":
        db.add(StudentProfile(user_id=user.id))
    elif data.role == "employer":
        if not data.company_name:
            raise HTTPException(status_code=400, detail="Company name required for employer")
        db.add(EmployerProfile(user_id=user.id, company_name=data.company_name))

    await db.commit()
    await db.refresh(user)

    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access=access,
        refresh=refresh,
        user=UserResponse.model_validate(user),
    )


@router.post("/login/", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access=access,
        refresh=refresh,
        user=UserResponse.model_validate(user),
    )


@router.post("/token/refresh/", response_model=dict)
async def refresh_token(data: RefreshRequest):
    payload = decode_token(data.refresh)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    access = create_access_token({"sub": user_id})
    refresh = create_refresh_token({"sub": user_id})

    return {"access": access, "refresh": refresh}


@router.get("/users/me/", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)


@router.get("/google/")
async def google_auth_redirect():
    from urllib.parse import urlencode
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    google_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return RedirectResponse(url=google_url)


@router.get("/google/callback/")
async def google_auth_callback(code: str = None, error: str = None, db: AsyncSession = Depends(get_db)):
    frontend = settings.FRONTEND_URL

    if error:
        return RedirectResponse(url=f"{frontend}/auth/login?error=google_denied")
    if not code:
        return RedirectResponse(url=f"{frontend}/auth/login?error=no_code")

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        token_json = token_resp.json()

    if "access_token" not in token_json:
        return RedirectResponse(url=f"{frontend}/auth/login?error=token_exchange_failed")

    async with httpx.AsyncClient() as client:
        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token_json['access_token']}"},
        )
        userinfo = userinfo_resp.json()

    email = userinfo.get("email")
    name = userinfo.get("name", "")
    avatar_url = userinfo.get("picture", "")

    if not email:
        return RedirectResponse(url=f"{frontend}/auth/login?error=no_email")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        if avatar_url and not user.avatar:
            user.avatar = avatar_url
        if name and not user.first_name:
            user.first_name = name.split(" ")[0]
            user.last_name = " ".join(name.split(" ")[1:]) if " " in name else ""
        await db.commit()
        await db.refresh(user)
    else:
        username = email.split("@")[0]
        base = username
        counter = 1
        while True:
            check = await db.execute(select(User).where(User.username == username))
            if not check.scalar_one_or_none():
                break
            username = f"{base}{counter}"
            counter += 1

        user = User(
            username=username,
            email=email,
            first_name=name.split(" ")[0] if name else "",
            last_name=" ".join(name.split(" ")[1:]) if " " in name else "",
            role="student",
            is_email_verified=True,
            avatar=avatar_url,
        )
        db.add(user)
        await db.flush()
        db.add(StudentProfile(user_id=user.id))
        await db.commit()
        await db.refresh(user)

    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})

    return RedirectResponse(
        url=f"{frontend}/auth/callback?access={access}&refresh={refresh}"
    )
