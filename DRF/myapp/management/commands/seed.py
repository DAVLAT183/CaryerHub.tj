from django.core.management.base import BaseCommand
from DRF.myapp.models import (
    User, StudentProfile, EmployerProfile,
    Category, Resume, Job, Application, Favorite,
    WorkSchedule, WorkFormat, WorkExperience, TariffPlan
)


class Command(BaseCommand):
    help = 'Заполняет базу данных демо-данными'

    def handle(self, *args, **options):
        self.stdout.write('Очистка старых данных...')
        Favorite.objects.all().delete()
        Application.objects.all().delete()
        Resume.objects.all().delete()
        Job.objects.all().delete()
        Category.objects.all().delete()
        WorkSchedule.objects.all().delete()
        WorkFormat.objects.all().delete()
        WorkExperience.objects.all().delete()
        EmployerProfile.objects.all().delete()
        StudentProfile.objects.all().delete()
        User.objects.all().delete()

        self.stdout.write('Создание тарифных планов...')
        tariffs_data = [
            {
                'name': 'free',
                'display_name': 'Бесплатный',
                'price': 0,
                'duration_days': 36500,
                'features': [
                    'Размещение 3 вакансий',
                    'Базовый поиск кандидатов',
                    'Чат с кандидатами',
                    'Email уведомления',
                ],
            },
            {
                'name': 'professional',
                'display_name': 'Профессиональный',
                'price': 299,
                'duration_days': 30,
                'features': [
                    'Безлимит вакансий',
                    'Расширенный поиск',
                    'Приоритет в выдаче',
                    'Аналитика просмотров',
                    'Выделение вакансии',
                    'Приоритетная поддержка',
                ],
            },
            {
                'name': 'corporate',
                'display_name': 'Корпоративный',
                'price': 999,
                'duration_days': 30,
                'features': [
                    'Всё из Профессионального',
                    'API доступ',
                    'Персональный менеджер',
                    'Кастомный брендинг',
                    'Интеграция с HR-системами',
                    'SLA 99.9%',
                ],
            },
        ]
        for td in tariffs_data:
            TariffPlan.objects.get_or_create(name=td['name'], defaults=td)

        self.stdout.write('Создание графиков работы...')
        schedules_data = [
            ('Гибкий', 'flexible'),
            ('2-4 часа', 'part_time'),
            ('Полная занятость', 'full_time'),
        ]
        schedules = {}
        for name, slug in schedules_data:
            s = WorkSchedule.objects.create(name=name, slug=slug)
            schedules[slug] = s

        self.stdout.write('Создание форматов работы...')
        formats_data = [
            ('Онлайн', 'online'),
            ('Офлайн', 'offline'),
            ('Гибрид', 'hybrid'),
        ]
        formats = {}
        for name, slug in formats_data:
            f = WorkFormat.objects.create(name=name, slug=slug)
            formats[slug] = f

        self.stdout.write('Создание опыта работы...')
        experiences_data = [
            ('Без опыта', 'no_experience'),
            ('До 1 года', 'up_to_1_year'),
            ('1-3 года', '1_3_years'),
            ('3-5 лет', '3_5_years'),
            ('Более 5 лет', 'more_than_5_years'),
        ]
        experiences = {}
        for name, slug in experiences_data:
            e = WorkExperience.objects.create(name=name, slug=slug)
            experiences[slug] = e

        self.stdout.write('Создание пользователей...')

        admin_user = User.objects.create_user(
            username='admin', email='admin@demo.com',
            password='demo1234', role='admin',
            first_name='Админ', last_name='Главный',
            is_staff=True, is_superuser=True
        )

        students_data = [
            {'username': 'ali', 'email': 'ali@student.com', 'role': 'student', 'phone': '+992900111222'},
            {'username': 'dilnoza', 'email': 'dilnoza@student.com', 'role': 'student', 'phone': '+992900333444'},
            {'username': 'sardor', 'email': 'sardor@student.com', 'role': 'student', 'phone': '+992900555666'},
            {'username': 'madina', 'email': 'madina@student.com', 'role': 'student', 'phone': '+992900777888'},
            {'username': 'farrukh', 'email': 'farrukh@student.com', 'role': 'student', 'phone': '+992900999000'},
            {'username': 'nilufar', 'email': 'nilufar@student.com', 'role': 'student', 'phone': '+992911222333'},
        ]

        students = []
        for s in students_data:
            user = User.objects.create_user(
                username=s['username'], email=s['email'],
                password='demo1234', role=s['role'], phone=s['phone'],
                first_name=s['username'].capitalize(), last_name='Тестов'
            )
            students.append(user)

        employers_data = [
            {'username': 'techsoft', 'email': 'hr@techsoft.tj', 'role': 'employer',
             'company': 'TechSoft TJ', 'desc': 'Разработка мобильных и веб-приложений. Более 50 проектов для государственных структур и частного сектора.',
             'website': 'https://techsoft.tj', 'address': 'Душанбе, пр. Рудаки 45', 'verified': True},
            {'username': 'digiart', 'email': 'jobs@digiart.tj', 'role': 'employer',
             'company': 'DigiArt Studio', 'desc': 'Креативное агентство по дизайну, брендингу и digital-маркетингу.',
             'website': 'https://digiart.tj', 'address': 'Душанбе, ул. Сафарова 12', 'verified': True},
            {'username': 'datahub', 'email': 'team@datahub.tj', 'role': 'employer',
             'company': 'DataHub Analytics', 'desc': 'Аналитика данных, машинное обучение и автоматизация бизнес-процессов.',
             'website': 'https://datahub.tj', 'address': 'Душанбе, ул. Навои 8', 'verified': True},
            {'username': 'cloudzone', 'email': 'info@cloudzone.tj', 'role': 'employer',
             'company': 'CloudZone', 'desc': 'Облачные решения, DevOps и инфраструктура для бизнеса. Работаем с AWS, Azure, GCP.',
             'website': 'https://cloudzone.tj', 'address': 'Худжанд, пр. Ленина 22', 'verified': False},
            {'username': 'webcraft', 'email': 'apply@webcraft.tj', 'role': 'employer',
             'company': 'WebCraft Studio', 'desc': 'Веб-разработка на React, Next.js, Vue. Создаём современные интерфейсы и SPA.',
             'website': 'https://webcraft.tj', 'address': 'Душанбе, ул. Тursunzoda 33', 'verified': True},
        ]

        employers = []
        for e in employers_data:
            user = User.objects.create_user(
                username=e['username'], email=e['email'],
                password='demo1234', role=e['role']
            )
            profile = EmployerProfile.objects.create(
                user=user, company_name=e['company'],
                description=e['desc'], website=e['website'],
                address=e['address'], is_verified=e['verified']
            )
            employers.append(profile)

        self.stdout.write('Создание профилей студентов...')
        students_profiles = []
        unis = ['ТНУ им. Ломоносова', 'ТГМУ', 'ТудAŞ', 'ХГУ', 'ТУСУР']
        faculties = ['ФИТ', 'ФМФ', 'Экономика', 'Юриспруденция', 'Инженерный']
        cities = ['Душанбе', 'Худжанд', 'Бохтар', 'Истаравшан', 'Куляб']

        for i, student in enumerate(students):
            profile = StudentProfile.objects.create(
                user=student,
                university=unis[i % len(unis)],
                faculty=faculties[i % len(faculties)],
                course=(i % 4) + 1,
                city=cities[i % len(cities)],
                age=19 + (i % 5),
            )
            students_profiles.append(profile)

        self.stdout.write('Создание категорий...')
        categories_data = [
            ('Программирование', 'programming'),
            ('Дизайн', 'design'),
            ('Маркетинг', 'marketing'),
            ('Копирайтинг', 'copywriting'),
            ('Аналитика', 'analytics'),
            ('Менеджмент', 'management'),
            ('SMM', 'smm'),
            ('Тестирование', 'testing'),
        ]
        categories = {}
        for name, slug in categories_data:
            cat = Category.objects.create(name=name, slug=slug)
            categories[slug] = cat

        self.stdout.write('Создание вакансий...')
        jobs_data = [
            {'employer': employers[0], 'cat': 'programming', 'title': 'Junior Frontend Developer',
             'desc': 'Ищем начинающего фронтенд-разработчика для работы с React/Next.js. Обучаем, помогаем расти. Возможен удалённый формат работы.',
             'salary_min': 5000, 'salary_max': 12000, 'schedule': 'flexible', 'format': 'online', 'exp': False,
             'sched_fk': 'flexible', 'fmt_fk': 'online', 'exp_fk': 'no_experience',
             'lat': 38.5598, 'lng': 68.7740, 'addr': 'Душанбе, пр. Рудаки 45'},
            {'employer': employers[0], 'cat': 'programming', 'title': 'Junior Python Developer',
             'desc': 'Разработка бэкенд-сервисов на Django/Django REST. Пишем API для мобильных приложений. Нужны знания Python и основ SQL.',
             'salary_min': 7000, 'salary_max': 15000, 'schedule': 'full_time', 'format': 'hybrid', 'exp': False,
             'sched_fk': 'full_time', 'fmt_fk': 'hybrid', 'exp_fk': 'no_experience',
             'lat': 38.5598, 'lng': 68.7740, 'addr': 'Душанбе, пр. Рудаки 45'},
            {'employer': employers[0], 'cat': 'programming', 'title': 'Стажёр DevOps Engineer',
             'desc': 'Помощь в настройке CI/CD пайплайнов, работа с Docker, Kubernetes, Linux. Идеально для студентов технических специальностей.',
             'salary_min': 4000, 'salary_max': 8000, 'schedule': 'part_time', 'format': 'online', 'exp': False,
             'sched_fk': 'part_time', 'fmt_fk': 'online', 'exp_fk': 'no_experience',
             'lat': 38.5598, 'lng': 68.7740, 'addr': 'Душанбе, пр. Рудаки 45'},
            {'employer': employers[1], 'cat': 'design', 'title': 'Junior UI/UX Designer',
             'desc': 'Дизайн интерфейсов для мобильных приложений и веб-сайтов. Работаем в Figma. Приветствуется портфолио.',
             'salary_min': 6000, 'salary_max': 13000, 'schedule': 'flexible', 'format': 'online', 'exp': False,
             'sched_fk': 'flexible', 'fmt_fk': 'online', 'exp_fk': 'no_experience',
             'lat': 38.5734, 'lng': 68.7836, 'addr': 'Душанбе, ул. Сафарова 12'},
            {'employer': employers[1], 'cat': 'design', 'title': 'Графический дизайнер',
             'desc': 'Создание рекламных баннеров, презентаций, branded контента. Photoshop, Illustrator, Figma.',
             'salary_min': 5000, 'salary_max': 10000, 'schedule': 'part_time', 'format': 'online', 'exp': False,
             'sched_fk': 'part_time', 'fmt_fk': 'online', 'exp_fk': 'no_experience',
             'lat': 38.5734, 'lng': 68.7836, 'addr': 'Душанбе, ул. Сафарова 12'},
            {'employer': employers[2], 'cat': 'analytics', 'title': 'Data Analyst (Junior)',
             'desc': 'Анализ данных, построение дашбордов, работа с SQL и Python (pandas). Помощь в принятии бизнес-решений.',
             'salary_min': 8000, 'salary_max': 18000, 'schedule': 'full_time', 'format': 'office', 'exp': True,
             'sched_fk': 'full_time', 'fmt_fk': 'offline', 'exp_fk': 'up_to_1_year',
             'lat': 38.5816, 'lng': 68.7638, 'addr': 'Душанбе, ул. Навои 8'},
            {'employer': employers[2], 'cat': 'marketing', 'title': 'Digital Marketing Intern',
             'desc': 'Помощь в запуске рекламных кампаний, анализ метрик, работа с Google Ads и Яндекс.Директ.',
             'salary_min': 3000, 'salary_max': 6000, 'schedule': 'part_time', 'format': 'hybrid', 'exp': False,
             'sched_fk': 'part_time', 'fmt_fk': 'hybrid', 'exp_fk': 'no_experience',
             'lat': 38.5816, 'lng': 68.7638, 'addr': 'Душанбе, ул. Навои 8'},
            {'employer': employers[3], 'cat': 'programming', 'title': 'Cloud Engineer (Trainee)',
             'desc': 'Настройка облачной инфраструктуры: AWS, GCP, Azure. Работа с Terraform, Ansible. Обучаем с нуля.',
             'salary_min': 5000, 'salary_max': 10000, 'schedule': 'flexible', 'format': 'online', 'exp': False,
             'sched_fk': 'flexible', 'fmt_fk': 'online', 'exp_fk': 'no_experience',
             'lat': 40.2829, 'lng': 69.6223, 'addr': 'Худжанд, пр. Ленина 22'},
            {'employer': employers[3], 'cat': 'testing', 'title': 'QA Tester (Junior)',
             'desc': 'Ручное тестирование веб-приложений. Составление тест-кейсов, баг-репортов. Знание Jira приветствуется.',
             'salary_min': 4000, 'salary_max': 8000, 'schedule': 'flexible', 'format': 'online', 'exp': False,
             'sched_fk': 'flexible', 'fmt_fk': 'online', 'exp_fk': 'no_experience',
             'lat': 40.2829, 'lng': 69.6223, 'addr': 'Худжанд, пр. Ленина 22'},
            {'employer': employers[4], 'cat': 'programming', 'title': 'Junior React Developer',
             'desc': 'Разработка SPA на React + TypeScript. Работа с REST API, Redux, TailwindCSS. Команда из 5 человек.',
             'salary_min': 6000, 'salary_max': 14000, 'schedule': 'full_time', 'format': 'hybrid', 'exp': False,
             'sched_fk': 'full_time', 'fmt_fk': 'hybrid', 'exp_fk': 'no_experience',
             'lat': 38.5600, 'lng': 68.7690, 'addr': 'Душанбе, ул. Тursunzoda 33'},
            {'employer': employers[4], 'cat': 'copywriting', 'title': 'Контент-менеджер',
             'desc': 'Написание статей для блога, SEO-оптимизация контента, работа с CMS. Нужен русский и таджикский языки.',
             'salary_min': 3500, 'salary_max': 7000, 'schedule': 'flexible', 'format': 'online', 'exp': False,
             'sched_fk': 'flexible', 'fmt_fk': 'online', 'exp_fk': 'no_experience',
             'lat': 38.5600, 'lng': 68.7690, 'addr': 'Душанбе, ул. Тursunzoda 33'},
            {'employer': employers[1], 'cat': 'smm', 'title': 'SMM-специалист',
             'desc': 'Ведение социальных сетей клиентов: Instagram, Telegram, TikTok. Создание контент-плана, аналитика охвата.',
             'salary_min': 4000, 'salary_max': 9000, 'schedule': 'flexible', 'format': 'online', 'exp': False,
             'sched_fk': 'flexible', 'fmt_fk': 'online', 'exp_fk': 'no_experience',
             'lat': 38.5734, 'lng': 68.7836, 'addr': 'Душанбе, ул. Сафарова 12'},
            {'employer': employers[0], 'cat': 'programming', 'title': 'Mobile Developer (Flutter)',
             'desc': 'Разработка кросс-платформенных мобильных приложений на Flutter/Dart. Опыт с Firebase приветствуется.',
             'salary_min': 8000, 'salary_max': 16000, 'schedule': 'full_time', 'format': 'office', 'exp': True,
             'sched_fk': 'full_time', 'fmt_fk': 'offline', 'exp_fk': '1_3_years',
             'lat': 38.5598, 'lng': 68.7740, 'addr': 'Душанбе, пр. Рудаки 45'},
            {'employer': employers[2], 'cat': 'analytics', 'title': 'Business Analyst Intern',
             'desc': 'Сбор требований, документирование процессов, работа со стейкхолдерами. Отличная возможность для старта карьеры.',
             'salary_min': 4000, 'salary_max': 7000, 'schedule': 'part_time', 'format': 'office', 'exp': False,
             'sched_fk': 'part_time', 'fmt_fk': 'offline', 'exp_fk': 'no_experience',
             'lat': 38.5816, 'lng': 68.7638, 'addr': 'Душанбе, ул. Навои 8'},
            {'employer': employers[3], 'cat': 'programming', 'title': 'Backend Developer (Go)',
             'desc': 'Микросервисы на Go, работа с gRPC, PostgreSQL. Высоконагруженные системы.',
             'salary_min': 10000, 'salary_max': 22000, 'schedule': 'full_time', 'format': 'hybrid', 'exp': True,
             'sched_fk': 'full_time', 'fmt_fk': 'hybrid', 'exp_fk': '3_5_years',
             'lat': 40.2829, 'lng': 69.6223, 'addr': 'Худжанд, пр. Ленина 22'},
            {'employer': employers[4], 'cat': 'design', 'desc': 'Motion-дизайн для рекламных роликов и презентаций. After Effects, Cinema 4D.',
             'title': 'Motion Designer', 'salary_min': 6000, 'salary_max': 12000,
             'schedule': 'flexible', 'format': 'online', 'exp': False,
             'sched_fk': 'flexible', 'fmt_fk': 'online', 'exp_fk': 'no_experience',
             'lat': 38.5600, 'lng': 68.7690, 'addr': 'Душанбе, ул. Тursunzoda 33'},
            {'employer': employers[1], 'cat': 'marketing', 'title': 'SEO-специалист',
             'desc': 'Продвижение сайтов, анализ конкурентов, работа с Ahrefs/Semrush, внутренняя и внешняя оптимизация.',
             'salary_min': 5000, 'salary_max': 11000, 'schedule': 'flexible', 'format': 'online', 'exp': False,
             'sched_fk': 'flexible', 'fmt_fk': 'online', 'exp_fk': 'no_experience',
             'lat': 38.5734, 'lng': 68.7836, 'addr': 'Душанбе, ул. Сафарова 12'},
            {'employer': employers[0], 'cat': 'programming', 'title': 'Стажёр Backend (Django)',
             'desc': 'Помощь в разработке REST API. Пишем тесты, документируем эндпоинты. Наставничество от сеньоров.',
             'salary_min': 3000, 'salary_max': 6000, 'schedule': 'part_time', 'format': 'remote', 'exp': False,
             'sched_fk': 'part_time', 'fmt_fk': 'online', 'exp_fk': 'no_experience',
             'lat': 38.5598, 'lng': 68.7740, 'addr': 'Душанбе, пр. Рудаки 45'},
            {'employer': employers[2], 'cat': 'analytics', 'title': 'ML Engineer (Junior)',
             'desc': 'Машинное обучение: классификация, предсказания, NLP. Python, scikit-learn, PyTorch.',
             'salary_min': 9000, 'salary_max': 20000, 'schedule': 'full_time', 'format': 'hybrid', 'exp': True,
             'sched_fk': 'full_time', 'fmt_fk': 'hybrid', 'exp_fk': 'up_to_1_year',
             'lat': 38.5816, 'lng': 68.7638, 'addr': 'Душанбе, ул. Навои 8'},
            {'employer': employers[4], 'cat': 'programming', 'title': 'Fullstack Developer',
             'desc': 'React + Django/Node.js. Полный цикл разработки от UI до деплоя. Ищем универсального разработчика.',
             'salary_min': 10000, 'salary_max': 20000, 'schedule': 'full_time', 'format': 'hybrid', 'exp': True,
             'sched_fk': 'full_time', 'fmt_fk': 'hybrid', 'exp_fk': '1_3_years',
             'lat': 38.5600, 'lng': 68.7690, 'addr': 'Душанбе, ул. Тursunzoda 33'},
        ]

        jobs = []
        for jd in jobs_data:
            job = Job.objects.create(
                employer=jd['employer'],
                category=categories[jd['cat']],
                title=jd['title'],
                description=jd['desc'],
                salary_min=jd['salary_min'],
                salary_max=jd['salary_max'],
                schedule=jd['schedule'],
                work_format=jd['format'],
                experience_required=jd['exp'],
                work_schedule=schedules[jd['sched_fk']],
                work_format_fk=formats[jd['fmt_fk']],
                experience=experiences[jd['exp_fk']],
                min_age=16,
                is_active=True,
                location_lat=jd['lat'],
                location_lng=jd['lng'],
                location_address=jd['addr'],
            )
            jobs.append(job)

        self.stdout.write('Создание резюме...')
        resumes_data = [
            {'profile': students_profiles[0], 'title': 'Frontend Developer',
             'about': 'Студент 3 курса ФИТ. Знаю React, TypeScript, TailwindCSS. Есть портфолио из 3 проектов.',
             'skills': ['React', 'TypeScript', 'JavaScript', 'HTML/CSS', 'Git'], 'sched': 'flexible', 'fmt': 'online',
             'sched_fk': 'flexible', 'fmt_fk': 'online'},
            {'profile': students_profiles[1], 'title': 'UI/UX Designer',
             'about': 'Дизайнер интерфейсов с опытом создания 5 мобильных приложений. Участник хакатонов.',
             'skills': ['Figma', 'Photoshop', 'Illustrator', 'Prototyping', 'User Research'], 'sched': 'part_time', 'fmt': 'online',
             'sched_fk': 'part_time', 'fmt_fk': 'online'},
            {'profile': students_profiles[2], 'title': 'Python Developer',
             'about': 'Знаю Python, Django, PostgreSQL. Писал API для учебных проектов. Интересуюсь ML.',
             'skills': ['Python', 'Django', 'SQL', 'REST API', 'Docker'], 'sched': 'full_time', 'fmt': 'hybrid',
             'sched_fk': 'full_time', 'fmt_fk': 'hybrid'},
            {'profile': students_profiles[3], 'title': 'Digital Marketing',
             'about': 'Вела Telegram-канал с 2к подписчиков. Знаю основы SMM, таргетированной рекламы.',
             'skills': ['SMM', 'Telegram', 'Canva', 'Analytics', 'Copywriting'], 'sched': 'flexible', 'fmt': 'online',
             'sched_fk': 'flexible', 'fmt_fk': 'online'},
            {'profile': students_profiles[4], 'title': 'QA Engineer',
             'about': 'Тестирую приложения в свободное время. Знаю Jira, тест-дизайн, API-тестирование.',
             'skills': ['Manual Testing', 'Jira', 'Postman', 'SQL', 'Test Cases'], 'sched': 'part_time', 'fmt': 'online',
             'sched_fk': 'part_time', 'fmt_fk': 'online'},
            {'profile': students_profiles[5], 'title': 'Content Manager',
             'about': 'Пишу статьи на русском и таджикском. Опыт работы с WordPress, SEO-оптимизация.',
             'skills': ['Copywriting', 'SEO', 'WordPress', 'Canva', 'Analytics'], 'sched': 'flexible', 'fmt': 'online',
             'sched_fk': 'flexible', 'fmt_fk': 'online'},
        ]

        resumes = []
        for rd in resumes_data:
            resume = Resume.objects.create(
                student=rd['profile'],
                title=rd['title'],
                about=rd['about'],
                skills=rd['skills'],
                schedule_type=rd['sched'],
                work_format=rd['fmt'],
                schedule=schedules[rd['sched_fk']],
                format=formats[rd['fmt_fk']],
            )
            resumes.append(resume)

        self.stdout.write('Создание откликов...')
        apps_data = [
            {'student_idx': 0, 'job_idx': 0, 'status': 'viewed', 'letter': 'Здравствуйте! Очень заинтересовала данная вакансия. Имею опыт с React и TypeScript, готов учиться и развиваться в вашей команде.'},
            {'student_idx': 0, 'job_idx': 9, 'status': 'interview', 'letter': 'Добрый день! Хотел бы пройти стажировку у вас. Умею работать с React, изучаю TypeScript.'},
            {'student_idx': 1, 'job_idx': 3, 'status': 'accepted', 'letter': 'Привет! Я UI/UX дизайнер, у меня есть портфолио. Буду рада работать в вашей студии!'},
            {'student_idx': 2, 'job_idx': 1, 'status': 'sent', 'letter': 'Здравствуйте, я студент-программист. Знаю Python и Django, хочу получить первый коммерческий опыт.'},
            {'student_idx': 2, 'job_idx': 7, 'status': 'viewed', 'letter': 'Интересует позиция Cloud Engineer. Есть базовые знания Linux и Docker.'},
            {'student_idx': 3, 'job_idx': 6, 'status': 'sent', 'letter': 'Привет! Опыт в SMM, ведение Telegram-каналов. Хочу попробовать себя в digital-маркетинге.'},
            {'student_idx': 4, 'job_idx': 8, 'status': 'interview', 'letter': 'Добрый день! Опыт ручного тестирования, составляю тест-кейсы и баг-репорты.'},
            {'student_idx': 5, 'job_idx': 10, 'status': 'rejected', 'letter': 'Здравствуйте! Пишу статьи на русском и таджикском, знакома с SEO.'},
        ]

        for ad in apps_data:
            Application.objects.create(
                job=jobs[ad['job_idx']],
                resume=resumes[ad['student_idx']],
                status=ad['status'],
                cover_letter=ad['letter'],
            )

        self.stdout.write('Создание избранного...')
        favs = [(0, 0), (0, 3), (0, 9), (1, 0), (2, 1), (3, 11), (4, 8)]
        for si, ji in favs:
            Favorite.objects.create(student=students_profiles[si], job=jobs[ji])

        self.stdout.write(self.style.SUCCESS(
            f'\nГотово! Создано:\n'
            f'  - 1 администратор (admin)\n'
            f'  - {len(students)} студентов + {len(employers)} работодателей\n'
            f'  - {len(categories_data)} категорий\n'
            f'  - {len(schedules_data)} графиков работы\n'
            f'  - {len(formats_data)} форматов работы\n'
            f'  - {len(experiences_data)} уровней опыта\n'
            f'  - {len(jobs_data)} вакансий\n'
            f'  - {len(resumes_data)} резюме\n'
            f'  - {len(apps_data)} откликов\n'
            f'  - {len(favs)} избранных\n'
            f'  - {len(tariffs_data)} тарифных планов\n'
            f'\nДемо пользователи (пароль: demo1234):\n'
            f'  admin       - Администратор (is_superuser)\n'
            f'  ali         - Студент\n'
            f'  techsoft    - Работодатель'
        ))
