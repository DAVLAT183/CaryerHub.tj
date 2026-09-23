#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, engine, async_session
from models import User, StudentProfile, EmployerProfile, Category, Job, Resume, TariffPlan, UserSubscription, Favorite, Notification
from sqlalchemy import select


async def seed_demo():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(User.metadata.create_all)  # This will create all tables based on Base
    
    async with async_session() as db:
        # Check if data already exists
        result = await db.execute(select(User))
        if result.scalar_one_or_none():
            print("✅ Demo data already exists, skipping...")
            return
        
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
        print(f"Created {len(categories)} categories")
        
        # Create tariff plans
        tariffs = [
            TariffPlan(name="Free", display_name="Бесплатный", price=0, duration_days=30, features=["5 резюме", "Отклики на вакансии"]),
            TariffPlan(name="Pro", display_name="Профи", price=999, duration_days=30, features=["Неограниченные резюме", "Приоритетные отклики", "Доступ к empleрам"]),
            TariffPlan(name="Premium", display_name="Премиум", price=1999, duration_days=30, features=["Все функции Pro", "Аналитика", "Поддержка"]),
        ]
        for tariff in tariffs:
            db.add(tariff)
        await db.flush()
        print(f"Created {len(tariffs)} tariff plans")
        
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
        print("Created admin user")
        
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
        print("Created employer user")
        
        # Create employer profile
        employer_profile = EmployerProfile(
            user_id=employer_user.id,
            company_name="Demo Company",
            description="Демо-компания для тестирования",
            website="https://demo.careerhub.local",
        )
        db.add(employer_profile)
        await db.flush()
        print("Created employer profile")
        
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
        print("Created student user")
        
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
        print("Created student profile")
        
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
        print("Created resume")
        
        # Create demo job
        demo_job = Job(
            employer_id=employer_profile.id,
            category_id=categories[0].id,
            title="Python Developer",
            description="Мы ищем опытного Python разработчика для работы над интересными проектами. Участие в разработке нашей платформы, работа с базами данных, реализация API.",
            salary_min=3000,
            salary_max=5000,
            schedule="full_time",
            work_format="hybrid",
            experience_required=True,
            is_active=True,
            source="manual",
            source_url="",
            source_id="",
            location_address="Душанбе, Таджикистан",
        )
        db.add(demo_job)
        await db.flush()
        print("Created demo job")
        
        # Create favorites for student
        favorite = Favorite(
            student_id=student_profile.id,
            job_id=demo_job.id,
        )
        db.add(favorite)
        print("Created favorite")
        
        # Create subscription
        subscription = UserSubscription(
            user_id=student_user.id,
            plan_id=1,  # Free plan
            status="active",
        )
        db.add(subscription)
        print("Created subscription")
        
        # Create notification
        notification = Notification(
            user_id=admin_user.id,
            notification_type="system",
            title="Система инициализирована",
            message="Демо данные успешно загружены в систему",
            link="/",
        )
        db.add(notification)
        print("Created notification")
        
        await db.commit()
        print("\n✅ Demo data seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_demo())