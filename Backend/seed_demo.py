#!/usr/bin/env python3
"""Idempotent demo-data seeder: safe to run against empty or existing DBs."""
import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))

from database import engine, async_session, init_db, _ensure_columns
from models import (
    User, StudentProfile, EmployerProfile, Category, Job, Resume,
    TariffPlan, UserSubscription, Favorite, Notification, NotificationPreference,
    Application, ChatSession, ChatMessage, DirectMessage, Payment,
    WorkSchedule, WorkFormat, WorkExperience,
)
from auth import hash_password
from sqlalchemy import select, func, text

CATEGORIES = [
    ("Программирование", "it"),
    ("Дизайн", "design"),
    ("Маркетинг", "marketing"),
    ("Продажи", "sales"),
    ("Финансы", "finance"),
    ("Логистика", "logistics"),
    ("Образование", "education"),
    ("Здравоохранение", "healthcare"),
    ("Строительство", "construction"),
    ("Транспорт", "transport"),
    ("Гостиничный бизнес", "hospitality"),
    ("Юриспруденция", "legal"),
    ("Медиа", "media"),
    ("HR", "hr"),
]

TARIFFS = [
    ("Free", "Бесплатный", 0, 30, ["5 резюме", "Отклики на вакансии"]),
    ("Pro", "Профи", 999, 30, ["Неограниченные резюме", "Приоритетные отклики", "Доступ к работодателям"]),
    ("Premium", "Премиум", 1999, 30, ["Все функции Pro", "Аналитика", "Поддержка"]),
]

WORK_SCHEDULES = [
    ("Полная занятость", "full_time"),
    ("Частичная занятость", "part_time"),
    ("Гибкий график", "flexible"),
    ("Сменный график", "shift"),
    ("Проектная работа", "project"),
]

WORK_FORMATS = [
    ("Офис", "offline"),
    ("Удалённо", "online"),
    ("Гибрид", "hybrid"),
]

WORK_EXPERIENCES = [
    ("Без опыта", "no_exp"),
    ("1–3 года", "1-3"),
    ("3–5 лет", "3-5"),
    ("Более 5 лет", "5+"),
]

DEMO_PASSWORD = "Demo1234!"

EMPLOYERS = [
    {
        "username": "employer_demo",
        "email": "employer@demo.local",
        "first_name": "Demo",
        "last_name": "Employer",
        "company": "Demo Company",
        "description": "Демо-компания для тестирования платформы CareerHub.",
        "website": "https://demo.careerhub.local",
        "address": "Душанбе, проспект Рудаки 1",
        "verified": True,
    },
    {
        "username": "techcorp_hr",
        "email": "hr@techcorp.local",
        "first_name": "Азиза",
        "last_name": "Каримова",
        "company": "TechCorp Tajikistan",
        "description": "IT-компания: разработка мобильных и веб-приложений, облачные решения.",
        "website": "https://techcorp.tj",
        "address": "Душанбе, ул. Сино 45",
        "verified": True,
    },
    {
        "username": "silkroad_hr",
        "email": "jobs@silkroad.local",
        "first_name": "Рустам",
        "last_name": "Назаров",
        "company": "Silk Road Digital",
        "description": "Цифровой маркетинг, e-commerce и логистические платформы для Центральной Азии.",
        "website": "https://silkroad.local",
        "address": "Душанбе, ул. Айни 12",
        "verified": True,
    },
    {
        "username": "pamir_jobs",
        "email": "hr@pamir.local",
        "first_name": "Малика",
        "last_name": "Шерозова",
        "company": "Pamir Services",
        "description": "Гостиничный бизнес, туризм и сервис в горных регионах Таджикистана.",
        "website": "https://pamir.tj",
        "address": "Хорог, ул. Ленина 3",
        "verified": False,
    },
]

STUDENTS = [
    {
        "username": "student_demo",
        "email": "student@demo.local",
        "first_name": "Demo",
        "last_name": "Student",
        "university": "Таджикский национальный университет",
        "faculty": "Факультет вычислительной техники и информационных технологий",
        "course": 3,
        "age": 24,
        "city": "Душанбе",
        "resume": {
            "title": "Python Developer Resume",
            "about": "Мотивированный разработчик Python с опытом 2 года. FastAPI, SQLAlchemy, Docker.",
            "skills": ["Python", "FastAPI", "SQLAlchemy", "Docker", "Git"],
            "schedule_type": "flexible",
            "work_format": "online",
            "github_url": "https://github.com/demo/user",
            "portfolio_url": "https://portfolio.demo.user",
            "linkedin_url": "https://linkedin.com/in/demo-user",
        },
    },
    {
        "username": "farhod_dev",
        "email": "farhod@demo.local",
        "first_name": "Фарход",
        "last_name": "Рахимов",
        "university": "Таджикский технический университет",
        "faculty": "Инженерный факультет ПО и АСУ",
        "course": 4,
        "age": 22,
        "city": "Душанбе",
        "resume": {
            "title": "Frontend Developer (React)",
            "about": "Разрабатываю интерфейсы на React/Next.js, знаю TypeScript и Tailwind.",
            "skills": ["React", "Next.js", "TypeScript", "Tailwind CSS", "REST API"],
            "schedule_type": "full_time",
            "work_format": "hybrid",
            "github_url": "https://github.com/farhod/dev",
            "portfolio_url": "https://farhod.dev",
            "linkedin_url": "",
        },
    },
    {
        "username": "nilufar_design",
        "email": "nilufar@demo.local",
        "first_name": "Нилуфар",
        "last_name": "Азизова",
        "university": "Таджикский государственный университет искусств имени М. Турсунзаде",
        "faculty": "Дизайн",
        "course": 2,
        "age": 21,
        "city": "Душанбе",
        "resume": {
            "title": "UI/UX Designer",
            "about": "Проектирую мобильные и веб-интерфейсы в Figma, собираю дизайн-системы.",
            "skills": ["Figma", "UI/UX", "Prototyping", "Adobe Illustrator"],
            "schedule_type": "flexible",
            "work_format": "online",
            "github_url": "",
            "portfolio_url": "https://nilufar.design",
            "linkedin_url": "",
        },
    },
    {
        "username": "bekzod_marketing",
        "email": "bekzod@demo.local",
        "first_name": "Бекзод",
        "last_name": "Умаров",
        "university": "Таджикский государственный университет коммерции",
        "faculty": "Менеджмент и маркетинг",
        "course": 3,
        "age": 23,
        "city": "Худжанд",
        "resume": {
            "title": "Digital Marketing Specialist",
            "about": "Веду SMM, контекстную рекламу и SEO для малого бизнеса.",
            "skills": ["SEO", "SMM", "Google Ads", "Analytics", "Copywriting"],
            "schedule_type": "full_time",
            "work_format": "hybrid",
            "github_url": "",
            "portfolio_url": "",
            "linkedin_url": "https://linkedin.com/in/bekzod",
        },
    },
]

# (employer_username, category_slug, title, description, sal_min, sal_max, schedule, format, exp, location, views)
JOBS = [
    ("employer_demo", "it", "Python Developer",
     "Разработка backend на FastAPI, работа с PostgreSQL/Docker, REST API. Команда 8 человек, гибрид.",
     3000, 5000, "full_time", "hybrid", True, "Душанбе, Таджикистан", 128),
    ("employer_demo", "design", "UI/UX Дизайнер",
     "Интерфейсы мобильных и веб-приложений, Figma, дизайн-системы, прототипирование.",
     2500, 4000, "full_time", "online", False, "Удалённо", 86),
    ("employer_demo", "marketing", "Digital Marketing Manager",
     "SEO, контекстная реклама, SMM, аналитика эффективности кампаний.",
     2000, 3500, "full_time", "hybrid", True, "Душанбе, Таджикистан", 54),
    ("employer_demo", "it", "Frontend Developer (React)",
     "React/Next.js, TypeScript, Tailwind. Для студентов без опыта — стажировка.",
     2000, 4000, "flexible", "online", False, "Удалённо", 112),
    ("employer_demo", "sales", "Менеджер по продажам",
     "Продажа IT-решений B2B, работа с базой клиентов, презентации, договоры.",
     1500, 3000, "full_time", "offline", False, "Душанбе, Таджикистан", 41),
    ("employer_demo", "finance", "Финансовый аналитик",
     "Бюджетирование, прогнозирование, Excel/1С/BI-инструменты.",
     2500, 4500, "full_time", "hybrid", True, "Душанбе, Таджикистан", 63),
    ("employer_demo", "it", "Стажёр-тестировщик QA",
     "Ручное тестирование веб-приложений, Jira, тест-кейсы. Обучение на месте.",
     800, 1500, "part_time", "online", False, "Удалённо", 97),
    ("employer_demo", "design", "Графический дизайнер",
     "Баннеры, презентации, рекламные материалы. Photoshop, Illustrator, After Effects.",
     1800, 3000, "flexible", "online", False, "Удалённо", 45),
    ("techcorp_hr", "it", "Mid Backend Engineer (Go)",
     "Микросервисы на Go, Kubernetes, Kafka. Опыт от 2 лет, зарплата по рынку.",
     4000, 7000, "full_time", "hybrid", True, "Душанбе, Таджикистан", 156),
    ("techcorp_hr", "it", "Mobile Developer (Flutter)",
     "Кроссплатформенная разработка, публикация в сторах, CI/CD.",
     2800, 4500, "full_time", "hybrid", False, "Душанбе, Таджикистан", 88),
    ("techcorp_hr", "hr", "HR Business Partner",
     "Подбор, адаптация, обучение, HR-бренд для IT-компании.",
     1800, 2800, "full_time", "hybrid", True, "Душанбе, Таджикистан", 33),
    ("techcorp_hr", "it", "DevOps Engineer",
     "AWS/GCP, Terraform, мониторинг, автоматизация деплоя.",
     4500, 6500, "full_time", "remote", True, "Удалённо", 74),
    ("techcorp_hr", "it", "Data Analyst",
     "SQL, Python, дашборды, продуктовая аналитика.",
     2200, 3800, "full_time", "hybrid", False, "Душанбе, Таджикистан", 61),
    ("silkroad_hr", "marketing", "SEO Specialist",
     "Технический и контентный SEO, ссылки, аналитика поиска.",
     1200, 2200, "flexible", "online", False, "Удалённо", 47),
    ("silkroad_hr", "marketing", "SMM Manager",
     "Ведение соцсетей, контент-план, работа с инфлюенсерами.",
     1000, 1800, "part_time", "online", False, "Худжанд", 39),
    ("silkroad_hr", "sales", "Key Account Manager",
     "Сопровождение ключевых клиентов, upsell, отчётность.",
     2000, 3500, "full_time", "offline", True, "Душанбе, Таджикистан", 28),
    ("silkroad_hr", "it", "E-commerce Manager",
     "Управление маркетплейсом, каталог, акции, аналитика продаж.",
     2000, 3200, "full_time", "hybrid", False, "Душанбе, Таджикистан", 52),
    ("silkroad_hr", "logistics", "Логист",
     "Планирование маршрутов, работа с перевозчиками, документооборот.",
     1500, 2500, "full_time", "offline", False, "Душанбе, Таджикистан", 22),
    ("pamir_jobs", "hospitality", "Гостьевой менеджер",
     "Приём гостей, бронирование, работа с PMS-системами.",
     1000, 1600, "shift", "offline", False, "Хорог", 18),
    ("pamir_jobs", "hospitality", "Повар",
     "Приготовление блюд национальной и европейской кухни, контроль качества.",
     1200, 2000, "full_time", "offline", True, "Хорог", 15),
    ("pamir_jobs", "education", "Преподаватель английского",
     "Индивидуальные и групповые занятия, подготовка к IELTS.",
     800, 1500, "flexible", "hybrid", False, "Душанбе, Таджикистан", 36),
    ("employer_demo", "legal", "Юрист по договорам",
     "Договорная работа, корпоративное право, консультации.",
     2000, 3500, "full_time", "hybrid", True, "Душанбе, Таджикистан", 25),
    ("techcorp_hr", "it", "QA Automation Engineer",
     "Playwright/pytest, CI-тесты, code review, работа в команде разработки.",
     2500, 4000, "full_time", "hybrid", True, "Душанбе, Таджикистан", 70),
    ("silkroad_hr", "media", "Контент-райтер",
     "Статьи, лендинги, email-рассылки. Портфолио обязательно.",
     900, 1600, "project", "online", False, "Удалённо", 31),
    ("employer_demo", "construction", "Сметчик",
     "Составление смет, работа с AutoCAD, контроль бюджета строительства.",
     1800, 3000, "full_time", "offline", True, "Душанбе, Таджикистан", 19),
    ("techcorp_hr", "it", "System Administrator",
     "Linux, Windows Server, сеть, backup, helpdesk L2.",
     1500, 2500, "full_time", "offline", False, "Душанбе, Таджикистан", 44),
    ("pamir_jobs", "transport", "Водитель кат. B",
     "Доставка по маршруту, уход за авто, отчётность.",
     700, 1200, "full_time", "offline", False, "Душанбе, Таджикистан", 27),
    ("employer_demo", "hr", "Recruiter",
     "Поиск кандидатов, телефонные интервью, ведение вакансий в ATS.",
     1200, 2000, "flexible", "hybrid", False, "Душанбе, Таджикистан", 38),
    ("silkroad_hr", "finance", "Бухгалтер",
     "Первичка, отчётность, 1С, взаимодейство��ие с проверяющими.",
     1600, 2600, "full_time", "offline", True, "Душанбе, Таджикистан", 34),
]


def _slug_exists(existing: set, slug: str) -> bool:
    return slug in existing


async def ensure_demo_data(db) -> dict:
    """Create missing demo entities. Idempotent — skips what already exists."""
    stats = {"categories": 0, "tariffs": 0, "lookups": 0, "users": 0, "jobs": 0,
             "resumes": 0, "applications": 0, "favorites": 0, "notifications": 0,
             "chats": 0, "messages": 0, "prefs": 0, "subscriptions": 0}

    # Categories (unique on name and slug — reuse if either matches)
    result = await db.execute(select(Category))
    existing_cats = list(result.scalars().all())
    existing_slugs = {c.slug for c in existing_cats}
    existing_names = {c.name for c in existing_cats}
    for name, slug in CATEGORIES:
        if slug not in existing_slugs and name not in existing_names:
            db.add(Category(name=name, slug=slug))
            existing_names.add(name)
            existing_slugs.add(slug)
            stats["categories"] += 1
    await db.flush()

    result = await db.execute(select(Category))
    all_cats = list(result.scalars().all())
    categories = {c.slug: c for c in all_cats}
    by_name = {c.name: c for c in all_cats}
    for name, slug in CATEGORIES:
        if slug not in categories and name in by_name:
            categories[slug] = by_name[name]

    # Tariffs
    result = await db.execute(select(TariffPlan.name))
    existing_tariffs = {row[0] for row in result.all()}
    for name, display, price, days, features in TARIFFS:
        if name not in existing_tariffs:
            db.add(TariffPlan(name=name, display_name=display, price=price,
                              duration_days=days, features=features))
            stats["tariffs"] += 1
    await db.flush()

    # Work schedules / formats / experiences
    result = await db.execute(select(WorkSchedule.slug))
    have_ws = {row[0] for row in result.all()}
    for name, slug in WORK_SCHEDULES:
        if slug not in have_ws:
            db.add(WorkSchedule(name=name, slug=slug))
            stats["lookups"] += 1

    result = await db.execute(select(WorkFormat.slug))
    have_wfmt = {row[0] for row in result.all()}
    for name, slug in WORK_FORMATS:
        if slug not in have_wfmt:
            db.add(WorkFormat(name=name, slug=slug))
            stats["lookups"] += 1

    result = await db.execute(select(WorkExperience.slug))
    have_we = {row[0] for row in result.all()}
    for name, slug in WORK_EXPERIENCES:
        if slug not in have_we:
            db.add(WorkExperience(name=name, slug=slug))
            stats["lookups"] += 1
    await db.flush()

    # Admin
    result = await db.execute(select(User).where(User.username == "admin"))
    admin_user = result.scalar_one_or_none()
    if not admin_user:
        admin_user = User(
            username="admin", email="admin@careerhub.local",
            first_name="Admin", last_name="User", role="staff",
            hashed_password=hash_password(DEMO_PASSWORD),
            is_active=True, is_staff=True, is_email_verified=True,
        )
        db.add(admin_user)
        await db.flush()
        stats["users"] += 1

    # Employers
    employers_by_name = {}
    for emp in EMPLOYERS:
        result = await db.execute(select(User).where(User.username == emp["username"]))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                username=emp["username"], email=emp["email"],
                first_name=emp["first_name"], last_name=emp["last_name"],
                role="employer", hashed_password=hash_password(DEMO_PASSWORD),
                is_active=True, is_email_verified=True, location="Душанбе",
            )
            db.add(user)
            await db.flush()
            stats["users"] += 1

        result = await db.execute(
            select(EmployerProfile).where(EmployerProfile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            profile = EmployerProfile(
                user_id=user.id, company_name=emp["company"],
                description=emp["description"], website=emp["website"],
                address=emp["address"], is_verified=emp["verified"],
            )
            db.add(profile)
            await db.flush()
            stats["users"] += 0
        employers_by_name[emp["username"]] = profile

    # Students + resumes
    students_by_name = {}
    resumes_by_name = {}
    for st in STUDENTS:
        result = await db.execute(select(User).where(User.username == st["username"]))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                username=st["username"], email=st["email"],
                first_name=st["first_name"], last_name=st["last_name"],
                role="student", hashed_password=hash_password(DEMO_PASSWORD),
                is_active=True, is_email_verified=True, location=st["city"],
            )
            db.add(user)
            await db.flush()
            stats["users"] += 1

        result = await db.execute(
            select(StudentProfile).where(StudentProfile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            profile = StudentProfile(
                user_id=user.id, university=st["university"],
                faculty=st["faculty"], course=st["course"],
                age=st["age"], city=st["city"],
                birth_date=f"{2026 - st['age']}-06-15",
            )
            db.add(profile)
            await db.flush()

        result = await db.execute(
            select(Resume).where(Resume.student_id == profile.id)
        )
        resume = result.scalar_one_or_none()
        if not resume:
            r = st["resume"]
            resume = Resume(
                student_id=profile.id, title=r["title"], about=r["about"],
                skills=r["skills"], schedule_type=r["schedule_type"],
                work_format=r["work_format"], github_url=r["github_url"],
                portfolio_url=r["portfolio_url"], linkedin_url=r["linkedin_url"],
            )
            db.add(resume)
            await db.flush()
            stats["resumes"] += 1

        students_by_name[st["username"]] = profile
        resumes_by_name[st["username"]] = resume

        # Notification prefs
        result = await db.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user.id)
        )
        if not result.scalar_one_or_none():
            db.add(NotificationPreference(user_id=user.id))
            stats["prefs"] += 1

        # Free subscription
        result = await db.execute(
            select(UserSubscription).where(UserSubscription.user_id == user.id)
        )
        if not result.scalar_one_or_none():
            free = await db.execute(select(TariffPlan).where(TariffPlan.name == "Free"))
            plan = free.scalar_one_or_none()
            if plan:
                db.add(UserSubscription(
                    user_id=user.id, plan_id=plan.id, status="active",
                    started_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=365),
                ))
                stats["subscriptions"] += 1
    await db.flush()

    # Jobs (skip titles that already exist for that employer)
    result = await db.execute(
        select(EmployerProfile.id, EmployerProfile.company_name)
    )
    # map by username via users
    emp_user_ids = {}
    for emp in EMPLOYERS:
        u = await db.execute(select(User.id).where(User.username == emp["username"]))
        uid = u.scalar_one_or_none()
        if uid:
            p = await db.execute(
                select(EmployerProfile).where(EmployerProfile.user_id == uid)
            )
            prof = p.scalar_one_or_none()
            if prof:
                emp_user_ids[emp["username"]] = prof.id

    result = await db.execute(select(Job.title))
    existing_titles = {row[0] for row in result.all()}

    jobs_created = []
    for emp_user, cat_slug, title, desc, smin, smax, sched, fmt, exp, loc, views in JOBS:
        if title in existing_titles:
            continue
        employer_id = emp_user_ids.get(emp_user)
        cat = categories.get(cat_slug)
        if not employer_id or not cat:
            continue
        work_fmt = "offline" if fmt == "remote" else fmt
        job = Job(
            employer_id=employer_id, category_id=cat.id, title=title,
            description=desc, salary_min=smin, salary_max=smax,
            schedule=sched, work_format=work_fmt, experience_required=exp,
            is_active=True, source="manual", location_address=loc,
            views_count=views,
        )
        db.add(job)
        jobs_created.append((title, cat_slug, emp_user))
        existing_titles.add(title)
        stats["jobs"] += 1
    await db.flush()

    # Favorites for first student
    student_profile = students_by_name.get("student_demo")
    if student_profile:
        result = await db.execute(
            select(Favorite).where(Favorite.student_id == student_profile.id)
        )
        have_fav = {row.job_id for row in result.scalars().all()}
        result = await db.execute(select(Job).where(Job.is_active == True).limit(5))
        for job in result.scalars().all():
            if job.id not in have_fav:
                db.add(Favorite(student_id=student_profile.id, job_id=job.id))
                stats["favorites"] += 1

    # Applications
    await db.flush()
    result = await db.execute(select(Job).where(Job.is_active == True).limit(12))
    jobs_pool = result.scalars().all()
    student_resumes = list(resumes_by_name.values())
    if student_resumes and jobs_pool:
        result = await db.execute(select(Application))
        have_pairs = {(a.job_id, a.resume_id) for a in result.scalars().all()}
        cover_letters = [
            "Здравствуйте! Готов(а) выйти на собеседование в удобное для вас время.",
            "Интересен проект, есть похожий опыт — приложил(а) резюме, буду рад(а) обсудить детали.",
            "Готов(а) начать стажировку с понедельника, быстро учусь и внимателен(на) к деталям.",
        ]
        statuses = ["sent", "reviewed", "interview", "accepted", "sent", "rejected"]
        for i, job in enumerate(jobs_pool[:8]):
            resume = student_resumes[i % len(student_resumes)]
            pair = (job.id, resume.id)
            if pair in have_pairs:
                continue
            db.add(Application(
                job_id=job.id, resume_id=resume.id,
                status=statuses[i % len(statuses)],
                cover_letter=cover_letters[i % len(cover_letters)],
            ))
            stats["applications"] += 1
            have_pairs.add(pair)

    # Notifications
    result = await db.execute(select(Notification).where(Notification.user_id == admin_user.id))
    if not result.scalars().first():
        db.add(Notification(
            user_id=admin_user.id, notification_type="system",
            title="Система инициализирована",
            message="Демо-данные успешно загружены в CareerHub",
            link="/",
        ))
        stats["notifications"] += 1

    student_user = await db.execute(select(User).where(User.username == "student_demo"))
    student_user = student_user.scalar_one_or_none()
    if student_user:
        result = await db.execute(select(Notification).where(Notification.user_id == student_user.id))
        if not result.scalars().first():
            for title, msg, link, ntype in [
                ("Новая вакансия для вас", "Frontend Developer (React) — подходящая вакансия", "/jobs", "job_match"),
                ("Отклик просмотрен", "TechCorp Tajikistan просмотрел ваше резюме", "/applications", "application_update"),
                ("Добро пожаловать", "Заполните профиль, чтобы получать точные рекомендации", "/settings", "system"),
            ]:
                db.add(Notification(
                    user_id=student_user.id, notification_type=ntype,
                    title=title, message=msg, link=link,
                ))
                stats["notifications"] += 1

    # AI chat session with sample messages
    if student_user:
        result = await db.execute(
            select(ChatSession).where(ChatSession.user_id == student_user.id)
        )
        session = result.scalar_one_or_none()
        if not session:
            session = ChatSession(user_id=student_user.id, title="Карьерный советник")
            db.add(session)
            await db.flush()
            stats["chats"] += 1
            db.add(ChatMessage(
                session_id=session.id, role="user",
                content="Какие навыки нужны junior Python разработчику?",
            ))
            db.add(ChatMessage(
                session_id=session.id, role="assistant",
                content=("Базово: Python, SQL, Git, HTTP/REST, основы ООП. "
                         "Практика через pet-проекты, понимание async, тесты и Docker "
                         "сильно выделяют кандидата на junior-вакансии."),
            ))
            stats["messages"] += 2

    # Direct messages student <-> employer
    if student_user:
        emp_user = await db.execute(select(User).where(User.username == "techcorp_hr"))
        emp_user = emp_user.scalar_one_or_none()
        if emp_user:
            result = await db.execute(
                select(DirectMessage).where(
                    (DirectMessage.sender_id == emp_user.id)
                    | (DirectMessage.recipient_id == emp_user.id)
                )
            )
            if not result.scalars().first():
                db.add(DirectMessage(
                    sender_id=emp_user.id, recipient_id=student_user.id,
                    content="Здравствуйте! Видели ваше резюме, готовы обсудить вакансию?",
                ))
                db.add(DirectMessage(
                    sender_id=student_user.id, recipient_id=emp_user.id,
                    content="Добрый день! Да, интересно — когда удобно созвониться?",
                    is_read=True,
                ))
                stats["messages"] += 2

    # Payment demo
    if student_user:
        result = await db.execute(select(Payment).where(Payment.user_id == student_user.id))
        if not result.scalars().first():
            sub = await db.execute(
                select(UserSubscription).where(UserSubscription.user_id == student_user.id)
            )
            sub = sub.scalars().first()
            if sub:
                db.add(Payment(
                    user_id=student_user.id, subscription_id=sub.id,
                    invoice_no="INV-DEMO-0001", amount=0, status="paid",
                    payment_method="demo", paid_at=datetime.now(timezone.utc),
                ))

    await db.commit()
    return stats


async def seed_demo():
    await init_db()  # create_all + column migration + basic seed path
    async with async_session() as db:
        stats = await ensure_demo_data(db)
    total = sum(stats.values())
    print("Demo seed stats:", stats)
    if total:
        print(f"OK: added {total} demo entities")
    else:
        print("OK: demo data already present")


if __name__ == "__main__":
    asyncio.run(seed_demo())
