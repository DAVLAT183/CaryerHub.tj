import asyncio
import httpx
import re
import json
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlencode
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session
from models import Job, EmployerProfile, Category


TAJIK_SOURCES = [
    {
        "name": "somon.tj",
        "base_url": "https://somon.tj",
        "jobs_url": "https://somon.tj/vakansii/",
        "is_tajik": True,
    },
]

FOREIGN_SOURCES = [
    {
        "name": "linkedin",
        "search_url": "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=remote&location=&start=",
        "is_tajik": False,
    },
    {
        "name": "remotive",
        "api_url": "https://remotive.com/api/remote-jobs?limit=50",
        "is_tajik": False,
    },
    {
        "name": "arbeitnow",
        "api_url": "https://www.arbeitnow.com/api/job-board-api",
        "is_tajik": False,
    },
    {
        "name": "himalayas",
        "api_url": "https://himalayas.app/jobs/api?limit=50",
        "is_tajik": False,
    },
]

CATEGORY_MAP = {
    "it": "Программирование",
    "programming": "Программирование",
    "developer": "Программирование",
    "design": "Дизайн",
    "marketing": "Маркетинг",
    "sales": "Продажи",
    "finance": "Финансы",
    "admin": "Администрирование",
    "hr": "HR",
    "engineering": "Инженерия",
    "education": "Образование",
    "other": "Другое",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}


async def _get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-2.5-flash")
    except Exception:
        return None


async def _ai_classify_job(title: str, description: str) -> dict:
    client = await _get_gemini_client()
    if not client:
        return _rule_based_classify(title, description)

    prompt = f"""Classify this job posting. Return ONLY valid JSON:
{{
  "category": "programming|design|marketing|analytics|other",
  "schedule": "flexible|part_time|full_time",
  "work_format": "online|offline|hybrid",
  "experience_required": true/false,
  "is_remote": true/false
}}

Title: {title}
Description: {description[:500]}"""

    try:
        response = client.generate_content(
            prompt,
            generation_config={"temperature": 0.3, "max_output_tokens": 256},
        )
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].rsplit("```", 1)[0].strip()
        elif "```" in text:
            text = text.split("```", 1)[1].rsplit("```", 1)[0].strip()
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start:end + 1])
    except Exception:
        pass

    return _rule_based_classify(title, description)


def _rule_based_classify(title: str, description: str) -> dict:
    text = f"{title} {description}".lower()

    category = "other"
    cat_keywords = {
        "programming": ["разработчик", "developer", "программ", "python", "javascript", "react", "node", "backend", "frontend", "fullstack", "it ", "coder"],
        "design": ["дизайнер", "design", "figma", "ui/ux", "graphic"],
        "marketing": ["маркетолог", "marketing", "seo", "реклам", "таргет"],
        "analytics": ["аналитик", "analyst", "данных", "data"],
    }
    for cat, keywords in cat_keywords.items():
        if any(k in text for k in keywords):
            category = cat
            break

    schedule = "flexible"
    if any(w in text for w in ["полн", "full-time", "full time"]):
        schedule = "full_time"
    elif any(w in text for w in ["частич", "part-time", "part time", "2-4"]):
        schedule = "part_time"

    work_format = "offline"
    if any(w in text for w in ["удалён", "удален", "remote", "онлайн", "из дома"]):
        work_format = "online"
    elif "гибрид" in text or "hybrid" in text:
        work_format = "hybrid"

    experience = any(w in text for w in ["опыт", "experience", "стаж", "senior", "middle"])

    is_remote = any(w in text for w in ["удалён", "удален", "remote", "online", "из дома", "в любой точке"])

    return {
        "category": category,
        "schedule": schedule,
        "work_format": work_format,
        "experience_required": experience,
        "is_remote": is_remote,
    }


def _parse_salary(text: str):
    if not text:
        return None, None
    text = text.replace(" ", "").replace("\xa0", "").replace("c.", "").replace("$", "").replace("€", "")
    numbers = re.findall(r"\d+", text)
    if len(numbers) >= 2:
        return int(numbers[0]), int(numbers[1])
    elif len(numbers) == 1:
        val = int(numbers[0])
        return val, val
    return None, None


async def _get_or_create_category(db: AsyncSession, name: str, slug: str):
    result = await db.execute(select(Category).where(Category.slug == slug))
    cat = result.scalar_one_or_none()
    if not cat:
        cat = Category(name=name, slug=slug)
        db.add(cat)
        await db.flush()
    return cat


async def _get_or_create_employer(db: AsyncSession, company_name: str):
    if not company_name:
        company_name = "Парсер (автоимпорт)"

    result = await db.execute(
        select(EmployerProfile).where(EmployerProfile.company_name == company_name)
    )
    emp = result.scalar_one_or_none()
    if emp:
        return emp

    from models import User
    from auth import hash_password

    username = company_name[:30].replace(" ", "_").lower() or "parser_bot"
    base = username
    counter = 1
    while True:
        check = await db.execute(select(User).where(User.username == username))
        if not check.scalar_one_or_none():
            break
        username = f"{base}_{counter}"
        counter += 1

    user = User(
        username=username,
        email=f"parser@{username}.local",
        role="employer",
        is_active=True,
        is_email_verified=True,
        first_name=company_name,
    )
    db.add(user)
    await db.flush()

    emp = EmployerProfile(
        user_id=user.id,
        company_name=company_name,
        description="Автоматический импорт вакансий",
    )
    db.add(emp)
    await db.flush()
    return emp


async def _save_job(db: AsyncSession, job_data: dict, source: str):
    source_id = job_data.get("source_id", "")
    if source_id:
        result = await db.execute(
            select(Job).where(Job.source == source, Job.source_id == source_id)
        )
        existing = result.scalar_one_or_none()
    else:
        existing = None

    ai_result = await _ai_classify_job(job_data.get("title", ""), job_data.get("description", ""))

    category_slug = ai_result.get("category", "other")
    category_name = CATEGORY_MAP.get(category_slug, "Другое")
    category = await _get_or_create_category(db, category_name, category_slug)

    employer = await _get_or_create_employer(db, job_data.get("company", ""))

    salary_min, salary_max = _parse_salary(job_data.get("salary_text", ""))

    if existing:
        existing.title = job_data.get("title", existing.title)
        existing.description = job_data.get("description", existing.description) or existing.description
        existing.salary_min = salary_min or existing.salary_min
        existing.salary_max = salary_max or existing.salary_max
        existing.category_id = category.id
        existing.employer_id = employer.id
        return existing, False
    else:
        job = Job(
            employer_id=employer.id,
            category_id=category.id,
            title=job_data.get("title", ""),
            description=job_data.get("description", ""),
            salary_min=salary_min,
            salary_max=salary_max,
            schedule=ai_result.get("schedule", "flexible"),
            work_format=ai_result.get("work_format", "offline"),
            experience_required=ai_result.get("experience_required", False),
            is_active=True,
            source=source,
            source_id=source_id,
            source_url=job_data.get("source_url", ""),
            location_address=job_data.get("location", ""),
        )
        db.add(job)
        return job, True


async def parse_somon_tj(db: AsyncSession, max_jobs: int = 30) -> dict:
    source = TAJIK_SOURCES[0]
    results = {"created": 0, "updated": 0, "errors": 0, "source": source["name"]}

    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        try:
            resp = await client.get(source["jobs_url"], headers=HEADERS)
            resp.raise_for_status()
        except Exception as e:
            return {"success": False, "error": str(e), **results}

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.find_all("div", attrs={"itemtype": "http://schema.org/JobPosting"})

        for card in cards[:max_jobs]:
            try:
                title_meta = card.find("meta", itemprop="title")
                title = title_meta["content"] if title_meta else ""

                desc_meta = card.find("meta", itemprop="description")
                description = desc_meta["content"] if desc_meta else ""

                link = card.find("a", href=True)
                if not link or not title:
                    continue

                job_url = urljoin(source["base_url"], link["href"])
                source_id_match = re.search(r"/adv/(\d+)", job_url)
                source_id = source_id_match.group(1) if source_id_match else ""

                company = ""
                for span in card.find_all("span"):
                    classes = " ".join(span.get("class", []))
                    text = span.get_text(strip=True)
                    if "font-bold" in classes and "text-sm" in classes and "bg-" not in classes:
                        if text and text not in ("VIP", "ТОП", "VIN"):
                            company = text
                            break

                location = ""
                muted_ps = card.find_all("p", class_=lambda c: c and "muted-foreground" in c)
                if muted_ps:
                    loc_text = muted_ps[-1].get_text(strip=True)
                    location = re.sub(r"\d+\s*(?:минут|час|день|дней?)\s*назад\s*", "", loc_text).strip()

                salary_span = card.find("span", class_=lambda c: c and "font-medium" in c and "text-base" in c)
                salary_text = salary_span.get_text(strip=True) if salary_span else ""

                job_data = {
                    "source_id": source_id,
                    "source_url": job_url,
                    "title": title,
                    "description": description,
                    "company": company,
                    "salary_text": salary_text,
                    "location": location,
                }

                _, created = await _save_job(db, job_data, source["name"])
                if created:
                    results["created"] += 1
                else:
                    results["updated"] += 1

                await asyncio.sleep(1)

            except Exception as e:
                results["errors"] += 1

    await db.commit()
    return {"success": True, **results}


async def parse_remotive(db: AsyncSession, max_jobs: int = 50) -> dict:
    source = FOREIGN_SOURCES[0]
    results = {"created": 0, "updated": 0, "errors": 0, "source": "remotive"}

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get("https://remotive.com/api/remote-jobs?limit=50")
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return {"success": False, "error": str(e), **results}

        jobs = data.get("jobs", [])
        for job in jobs[:max_jobs]:
            try:
                title = job.get("title", "")
                description = job.get("description", "")
                company = job.get("company_name", "")
                salary = job.get("salary", "")
                url = job.get("url", "")
                source_id = str(job.get("id", ""))

                job_data = {
                    "source_id": source_id,
                    "source_url": url,
                    "title": title,
                    "description": description,
                    "company": company,
                    "salary_text": salary,
                    "location": "Remote",
                }

                _, created = await _save_job(db, job_data, "remotive")
                if created:
                    results["created"] += 1
                else:
                    results["updated"] += 1

            except Exception:
                results["errors"] += 1

    await db.commit()
    return {"success": True, **results}


async def parse_arbeitnow(db: AsyncSession, max_jobs: int = 50) -> dict:
    results = {"created": 0, "updated": 0, "errors": 0, "source": "arbeitnow"}

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get("https://www.arbeitnow.com/api/job-board-api")
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return {"success": False, "error": str(e), **results}

        jobs = data.get("data", [])
        for job in jobs[:max_jobs]:
            try:
                title = job.get("title", "")
                description = job.get("description", "")
                company = job.get("company_name", "")
                url = job.get("url", "")
                source_id = str(job.get("id", ""))
                remote = job.get("remote", False)
                location = job.get("location", "")

                if not remote:
                    continue

                job_data = {
                    "source_id": source_id,
                    "source_url": url,
                    "title": title,
                    "description": description,
                    "company": company,
                    "salary_text": "",
                    "location": location or "Remote",
                }

                _, created = await _save_job(db, job_data, "arbeitnow")
                if created:
                    results["created"] += 1
                else:
                    results["updated"] += 1

            except Exception:
                results["errors"] += 1

    await db.commit()
    return {"success": True, **results}


async def parse_himalayas(db: AsyncSession, max_jobs: int = 50) -> dict:
    results = {"created": 0, "updated": 0, "errors": 0, "source": "himalayas"}

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get("https://himalayas.app/jobs/api?limit=50")
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return {"success": False, "error": str(e), **results}

        jobs = data.get("jobs", [])
        for job in jobs[:max_jobs]:
            try:
                title = job.get("title", "")
                description = job.get("description", "")
                company = job.get("companyName", "")
                url = job.get("url", "")
                source_id = str(job.get("id", ""))
                location = job.get("location", "")

                job_data = {
                    "source_id": source_id,
                    "source_url": f"https://himalayas.app/jobs/{source_id}" if not url else url,
                    "title": title,
                    "description": description,
                    "company": company,
                    "salary_text": "",
                    "location": location or "Remote",
                }

                _, created = await _save_job(db, job_data, "himalayas")
                if created:
                    results["created"] += 1
                else:
                    results["updated"] += 1

            except Exception:
                results["errors"] += 1

    await db.commit()
    return {"success": True, **results}


async def parse_all_sources(max_jobs_per_source: int = 30) -> dict:
    all_results = []

    async with async_session() as db:
        tasks = [
            ("somon.tj", parse_somon_tj(db, max_jobs_per_source)),
            ("remotive", parse_remotive(db, max_jobs_per_source)),
            ("arbeitnow", parse_arbeitnow(db, max_jobs_per_source)),
            ("himalayas", parse_himalayas(db, max_jobs_per_source)),
        ]

        for name, coro in tasks:
            try:
                result = await coro
                all_results.append(result)
            except Exception as e:
                all_results.append({"source": name, "success": False, "error": str(e)})

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": all_results,
    }
