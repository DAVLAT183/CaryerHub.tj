from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session


async def _ensure_columns(conn):
    """SQLite does not ALTER TABLE on create_all — add columns missing from older DBs."""
    from sqlalchemy import text, inspect

    def _run(sync_conn):
        inspector = inspect(sync_conn)
        wanted = {
            "jobs": {"views_count": "INTEGER DEFAULT 0"},
            "student_profiles": {"views_count": "INTEGER DEFAULT 0"},
            "employer_profiles": {"views_count": "INTEGER DEFAULT 0"},
        }
        for table, columns in wanted.items():
            if table not in inspector.get_table_names():
                continue
            existing = {c["name"] for c in inspector.get_columns(table)}
            for name, ddl_type in columns.items():
                if name not in existing:
                    sync_conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl_type}")
                    )

    await conn.run_sync(_run)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _ensure_columns(conn)

    # Seed demo data after tables are created
    from models import User, StudentProfile, EmployerProfile, Category, Job, Resume, TariffPlan, UserSubscription, Favorite, Notification
    from sqlalchemy import select, func
    
    async with async_session() as db:
        # Check if demo data already exists
        result = await db.execute(select(func.count(Job.id)))
        job_count = result.scalar() or 0
        if job_count > 0:
            return  # Data already seeded
        
        # Create categories
        categories = [
            Category(name="Программирование", slug="it"),
            Category(name="Дизайн", slug="design"),
            Category(name="Маркетинг", slug="marketing"),
            Category(name="Продажи", slug="sales"),
            Category(name="Финансы", slug="finance"),
        ]
        for cat in categories:
            db.add(cat)
        await db.flush()
        
        # Create tariff plans
        tariffs = [
            TariffPlan(name="Free", display_name="Бесплатный", price=0, duration_days=30, features=["5 резюме", "Отклики на вакансии"]),
            TariffPlan(name="Pro", display_name="Профи", price=999, duration_days=30, features=["Неограниченные резюме", "Приоритетные отклики", "Доступ к empleрам"]),
            TariffPlan(name="Premium", display_name="Премиум", price=1999, duration_days=30, features=["Все функции Pro", "Аналитика", "Поддержка"]),
        ]
        for tariff in tariffs:
            db.add(tariff)
        await db.flush()
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@careerhub.local",
            first_name="Admin",
            last_name="User",
            role="staff",
            is_active=True,
            is_staff=True,
            is_email_verified=True,
        )
        db.add(admin_user)
        await db.flush()
        
        # Create employer user
        employer_user = User(
            username="employer_demo",
            email="employer@demo.local",
            first_name="Demo",
            last_name="Employer",
            role="employer",
            is_active=True,
            is_email_verified=True,
        )
        db.add(employer_user)
        await db.flush()
        
        # Create employer profile
        employer_profile = EmployerProfile(
            user_id=employer_user.id,
            company_name="Demo Company",
            description="Демо-компания для тестирования",
            website="https://demo.careerhub.local",
        )
        db.add(employer_profile)
        await db.flush()
        
        # Create student user
        student_user = User(
            username="student_demo",
            email="student@demo.local",
            first_name="Demo",
            last_name="Student",
            role="student",
            is_active=True,
            is_email_verified=True,
        )
        db.add(student_user)
        await db.flush()
        
        # Create student profile
        student_profile = StudentProfile(
            user_id=student_user.id,
            university="Темурский национальный университет",
            faculty="Факультет вычислительной техники и информационных технологий",
            course=3,
            birth_date="2000-01-01",
            age=24,
            city="Душанбе",
        )
        db.add(student_profile)
        await db.flush()
        
        # Create resume
        resume = Resume(
            student_id=student_profile.id,
            title="Python Developer Resume",
            about="Мотивированный разработчик Python с опытом работы 2 года. Умею FastAPI, SQLAlchemy, Docker.",
            skills=["Python", "FastAPI", "SQLAlchemy", "Docker", "Git"],
            schedule_type="flexible",
            work_format="online",
            github_url="https://github.com/demo/user",
            portfolio_url="https://portfolio.demo.user",
            linkedin_url="https://linkedin.com/in/demo-user",
        )
        db.add(resume)
        await db.flush()
        
        # Create demo jobs
        demo_jobs_data = [
            {
                "category_id": categories[0].id,
                "title": "Python Developer",
                "description": "Мы ищем опытного Python разработчика для работы над интересными проектами. Участие в разработке нашей платформы, работа с базами данных, реализация API. Стек: FastAPI, PostgreSQL, Docker.",
                "salary_min": 3000, "salary_max": 5000,
                "schedule": "full_time", "work_format": "hybrid",
                "experience_required": True, "location_address": "Душанбе, Таджикистан",
            },
            {
                "category_id": categories[1].id,
                "title": "UI/UX Дизайнер",
                "description": "Ищем талантливого дизайнера для создания интерфейсов мобильных и веб-приложений. Работа в Figma, создание дизайн-систем, прототипирование.",
                "salary_min": 2500, "salary_max": 4000,
                "schedule": "full_time", "work_format": "online",
                "experience_required": False, "location_address": "Удалённо",
            },
            {
                "category_id": categories[2].id,
                "title": "Digital Marketing Manager",
                "description": "Управление цифровыми маркетинговыми кампаниями: SEO, контекстная реклама, SMM. Анализ эффективности и оптимизация стратегий.",
                "salary_min": 2000, "salary_max": 3500,
                "schedule": "full_time", "work_format": "hybrid",
                "experience_required": True, "location_address": "Душанбе, Таджикистан",
            },
            {
                "category_id": categories[0].id,
                "title": "Frontend Developer (React)",
                "description": "Разработка пользовательских интерфейсов на React/Next.js. Работа с TypeScript, Tailwind CSS, REST API. Для студентов без опыта — стажировка.",
                "salary_min": 2000, "salary_max": 4000,
                "schedule": "flexible", "work_format": "online",
                "experience_required": False, "location_address": "Удалённо",
            },
            {
                "category_id": categories[3].id,
                "title": "Менеджер по продажам",
                "description": "Продажа IT-решений корпоративным клиентам. Работа с базой клиентов, проведение презентаций, заключение договоров.",
                "salary_min": 1500, "salary_max": 3000,
                "schedule": "full_time", "work_format": "offline",
                "experience_required": False, "location_address": "Душанбе, Таджикистан",
            },
            {
                "category_id": categories[4].id,
                "title": "Финансовый аналитик",
                "description": "Анализ финансовой отчётности, бюджетирование, прогнозирование. Работа с Excel, 1С, BI-инструментами.",
                "salary_min": 2500, "salary_max": 4500,
                "schedule": "full_time", "work_format": "hybrid",
                "experience_required": True, "location_address": "Душанбе, Таджикистан",
            },
            {
                "category_id": categories[0].id,
                "title": "Стажёр-тестировщик QA",
                "description": "Ищем начинающего тестировщика для ручного тестирования веб-приложений. Обучение на месте, работа с Jira, составление тест-кейсов.",
                "salary_min": 800, "salary_max": 1500,
                "schedule": "part_time", "work_format": "online",
                "experience_required": False, "location_address": "Удалённо",
            },
            {
                "category_id": categories[1].id,
                "title": "Графический дизайнер",
                "description": "Создание визуального контента: баннеры, презентации, рекламные материалы. Adobe Photoshop, Illustrator, After Effects.",
                "salary_min": 1800, "salary_max": 3000,
                "schedule": "flexible", "work_format": "online",
                "experience_required": False, "location_address": "Удалённо",
            },
        ]

        demo_jobs = []
        for jd in demo_jobs_data:
            job = Job(
                employer_id=employer_profile.id,
                is_active=True,
                source="manual",
                source_url="",
                source_id="",
                **jd,
            )
            db.add(job)
            demo_jobs.append(job)
        await db.flush()

        # Create favorites for student
        favorite = Favorite(
            student_id=student_profile.id,
            job_id=demo_jobs[0].id,
        )
        db.add(favorite)
        
        # Create subscription
        subscription = UserSubscription(
            user_id=student_user.id,
            plan_id=1,  # Free plan
            status="active",
        )
        db.add(subscription)
        
        # Create notification
        notification = Notification(
            user_id=admin_user.id,
            notification_type="system",
            title="Система инициализирована",
            message="Демо данные успешно загружены в систему",
            link="/",
        )
        db.add(notification)
        
        await db.commit()
        print("✅ Demo data seeded successfully")
