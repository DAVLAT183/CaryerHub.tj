import json
import os
import random
from django.conf import settings


def _get_gemini_client():
    api_key = os.environ.get('GEMINI_API_KEY', getattr(settings, 'GEMINI_API_KEY', ''))
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.5-flash')
    except Exception:
        return None


SKILL_SUGGESTIONS = {
    'programming': {
        'hard': ['Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'Go', 'Rust', 'PHP', 'Swift', 'Kotlin'],
        'soft': ['Аналитическое мышление', 'Работа в команде', 'Адаптивность', 'Стремление к обучению'],
        'tools': ['Git', 'Docker', 'PostgreSQL', 'Redis', 'REST API', 'GraphQL', 'Linux', 'CI/CD'],
    },
    'design': {
        'hard': ['Figma', 'Adobe Photoshop', 'Adobe Illustrator', 'Adobe XD', 'Sketch', 'InVision', 'Protopie'],
        'soft': ['Креативность', 'Внимание к деталям', 'Эмпатия к пользователю', 'Презентация идей'],
        'tools': ['Maze', 'Hotjar', 'Principle', 'After Effects', 'CSS', 'HTML'],
    },
    'marketing': {
        'hard': ['Яндекс.Директ', 'Google Ads', 'Таргетированная реклама', 'SEO', 'SERM', 'Контент-маркетинг'],
        'soft': ['Креативность', 'Аналитический склад ума', 'Коммуникабельность', 'Стратегическое мышление'],
        'tools': ['Яндекс.Метрика', 'Google Analytics', 'Canva', 'Bitrix24', 'Ahrefs', 'SimilarWeb'],
    },
    'analytics': {
        'hard': ['SQL', 'Python', 'Excel', 'Power BI', 'Tableau', 'Статистика', 'Pandas', 'NumPy'],
        'soft': ['Аналитическое мышление', 'Внимание к деталям', 'Структурное мышление', 'Находчивость'],
        'tools': ['Jupyter Notebook', 'Google Sheets', 'PostgreSQL', 'ClickHouse', 'Amplitude'],
    },
    'copywriting': {
        'hard': ['Копирайтинг', 'Рерайтинг', 'SEO-тексты', 'Сторителлинг', 'Тексты для соцсетей', 'Рекламные тексты'],
        'soft': ['Грамотность', 'Креативность', 'Умение работать с ТЗ', 'Тайм-менеджмент'],
        'tools': ['TM Guru', 'Advego', 'Text.ru', 'Яндекс.Вордстат', 'Google Docs'],
    },
    'smm': {
        'hard': ['Instagram', 'Telegram', 'VK', 'TikTok', 'Facebook', 'Контент-план', 'Таргет'],
        'soft': ['Креативность', 'Коммуникабельность', 'Аналитический склад ума', 'Тайм-менеджмент'],
        'tools': ['Canva', 'Figma', 'VK Ads', 'MyTarget', 'TargetHunter', 'SendPulse'],
    },
    'management': {
        'hard': ['Управление проектами', 'Agile', 'Scrum', 'Kanban', 'MS Project', 'Jira', 'Confluence'],
        'soft': ['Лидерство', 'Коммуникация', 'Negotiation', 'Делегирование', 'Стрессоустойчивость'],
        'tools': ['Jira', 'Trello', 'Notion', 'Google Workspace', 'MS Office', 'Slack'],
    },
}


def _build_user_profile(student_profile):
    user = student_profile.user
    profile_data = {
        'username': user.username,
        'university': student_profile.university or '',
        'faculty': student_profile.faculty or '',
        'course': student_profile.course or 0,
        'city': student_profile.city or '',
        'age': student_profile.age or 0,
    }

    category_keywords = {}
    faculty_lower = (student_profile.faculty or '').lower()
    if any(w in faculty_lower for w in ['информац', 'кибернет', 'программ', 'вычисл', 'математ', 'технол']):
        category_keywords['programming'] = 3
        category_keywords['analytics'] = 1
    if any(w in faculty_lower for w in ['дизайн', 'искусств', 'архитектур', 'визуал']):
        category_keywords['design'] = 3
    if any(w in faculty_lower for w in ['маркетинг', 'реклам', 'коммуникац', 'журналист', 'PR', 'связ']):
        category_keywords['marketing'] = 3
        category_keywords['copywriting'] = 1
        category_keywords['smm'] = 2
    if any(w in faculty_lower for w in ['эконом', 'финанс', 'менеджмент', 'управлен', 'бизнес']):
        category_keywords['analytics'] = 2
        category_keywords['management'] = 2
    if any(w in faculty_lower for w in ['филолог', 'лингвист', 'иностран', 'перевод']):
        category_keywords['copywriting'] = 3
        category_keywords['smm'] = 1

    if not category_keywords:
        category_keywords = {'programming': 1, 'marketing': 1, 'analytics': 1, 'design': 1, 'copywriting': 1}

    return profile_data, category_keywords


def _generate_resume_rule_based(student_profile):
    profile_data, category_keywords = _build_user_profile(student_profile)

    top_categories = sorted(category_keywords.items(), key=lambda x: x[1], reverse=True)[:2]
    primary_category = top_categories[0][0] if top_categories else 'programming'

    skills_data = SKILL_SUGGESTIONS.get(primary_category, SKILL_SUGGESTIONS['programming'])

    hard_skills = random.sample(skills_data['hard'], min(4, len(skills_data['hard'])))
    soft_skills = random.sample(skills_data['soft'], min(2, len(skills_data['soft'])))
    tools = random.sample(skills_data['tools'], min(3, len(skills_data['tools'])))
    all_skills = hard_skills + tools + soft_skills

    course = profile_data.get('course', 1)
    city = profile_data.get('city', 'не указан')
    university = profile_data.get('university', 'не указан')

    title_variants = {
        'programming': [
            f'{hard_skills[0]}-разработчик' if hard_skills else 'Разработчик',
            'Junior Backend Developer',
            'Junior Frontend Developer',
            'Python Developer',
        ],
        'design': [
            'UI/UX дизайнер',
            'Графический дизайнер',
            'Product Designer',
        ],
        'marketing': [
            'Digital-маркетолог',
            'SMM-специалист',
            'Маркетолог',
        ],
        'analytics': [
            'Data Analyst',
            'Аналитик данных',
            'Business Analyst',
        ],
        'copywriting': [
            'Копирайтер',
            'Контент-менеджер',
            'Контент-мейкер',
        ],
        'smm': [
            'SMM-менеджер',
            'Контент-менеджер',
            'Маркетолог',
        ],
        'management': [
            'Project Manager',
            'Product Manager',
            'Менеджер по проектам',
        ],
    }
    titles = title_variants.get(primary_category, ['Специалист'])
    title = random.choice(titles)

    descriptions = {
        'programming': (
            f'Студент {course} курса {university}. '
            f'Имею实践经验 с {", ".join(hard_skills[:3])}. '
            f'Знаком с {", ".join(tools[:2])}. '
            f'Быстро обучаюсь, люблю решать сложные задачи. '
            f'Ищу стажировку или junior-позицию для развития в IT.'
        ),
        'design': (
            f'Студент {course} курса {university}. '
            f'Работаю с {", ".join(hard_skills[:3])}. '
            f'Создаю удобные интерфейсы, следую трендам в дизайне. '
            f'Есть портфолио. Ищу стажировку в продуктовой команде.'
        ),
        'marketing': (
            f'Студент {course} курса {university}. '
            f'Опыт с {", ".join(hard_skills[:3])}. '
            f'Понимаю аналитику, умею строить стратегии продвижения. '
            f'Ищу стажировку в маркетинг или рекламный отдел.'
        ),
        'analytics': (
            f'Студент {course} курса {university}. '
            f'Знаю {", ".join(hard_skills[:3])}. '
            f'Умею работать с данными, строить дашборды и находить инсайты. '
            f'Ищу стажировку в аналитический отдел.'
        ),
        'copywriting': (
            f'Студент {course} курса {university}. '
            f'Пишу тексты для {", ".join(random.sample(["блогов", "рассылок", "лендингов", "соцсетей", "рекламы"], 2))}. '
            f'Грамотный, креативный, ответственный. Ищу удалённую работу.'
        ),
        'smm': (
            f'Студент {course} курса {university}. '
            f'Веду аккаунты в {", ".join(random.sample(["Instagram", "Telegram", "VK", "TikTok"], 2))}. '
            f'Создаю контент-планы, работаю с таргетом. Ищу стажировку.'
        ),
        'management': (
            f'Студент {course} курса {university}. '
            f'Знаком с {", ".join(random.sample(["Agile", "Scrum", "Kanban", "Jira"], 2))}. '
            f'Организую командную работу, умею расставлять приоритеты. '
            f'Ищу стажировку в проектный отдел.'
        ),
    }
    about = descriptions.get(primary_category, f'Студент {university}. Ищу работу.')

    schedule_preferences = ['flexible', 'part_time']
    format_preferences = ['online', 'hybrid']

    return {
        'title': title,
        'about': about,
        'skills': all_skills,
        'schedule_type': random.choice(schedule_preferences),
        'work_format': random.choice(format_preferences),
        'category': primary_category,
    }


def _generate_resume_ai(student_profile):
    client = _get_gemini_client()
    if not client:
        return _generate_resume_rule_based(student_profile)

    user = student_profile.user
    prompt = f"""Ты — карьерный консультант. Сгенерируй резюме для студента.

Данные студента:
- Имя: {user.username}
- Университет: {student_profile.university or 'Не указан'}
- Факультет: {student_profile.faculty or 'Не указан'}
- Курс: {student_profile.course or 'Не указан'}
- Город: {student_profile.city or 'Не указан'}
- Возраст: {student_profile.age or 'Не указан'}

Верни JSON без markdown с полями:
- title: желаемая должность (1 строка)
- about: текст "О себе" (3-5 предложений, профессиональный тон)
- skills: массив из 6-10 навыков (хард скилы + инструменты + софт скилы)
- schedule_type: один из "flexible", "part_time", "full_time"
- work_format: один из "online", "offline", "hybrid"
- category: категория вакансий - один из "programming", "design", "marketing", "analytics", "copywriting", "smm", "management"

Отвечай ТОЛЬКО валидным JSON, без пояснений."""

    try:
        response = client.generate_content(
            prompt,
            generation_config={
                'temperature': 0.7,
                'max_output_tokens': 2048,
            },
        )
        content = response.text.strip()

        if '```json' in content:
            content = content.split('```json', 1)[1].rsplit('```', 1)[0].strip()
        elif '```' in content:
            content = content.split('```', 1)[1].rsplit('```', 1)[0].strip()

        json_start = content.find('{')
        json_end = content.rfind('}')
        if json_start != -1 and json_end != -1:
            content = content[json_start:json_end + 1]

        result = json.loads(content)

        required_fields = ['title', 'about', 'skills', 'schedule_type', 'work_format', 'category']
        for field in required_fields:
            if field not in result:
                return _generate_resume_rule_based(student_profile)

        if result['schedule_type'] not in ['flexible', 'part_time', 'full_time']:
            result['schedule_type'] = 'flexible'
        if result['work_format'] not in ['online', 'offline', 'hybrid']:
            result['work_format'] = 'online'
        if result['category'] not in SKILL_SUGGESTIONS:
            result['category'] = 'programming'

        return result
    except Exception:
        return _generate_resume_rule_based(student_profile)


def generate_resume(student_profile):
    return _generate_resume_ai(student_profile)


def _chat_with_gemini(messages, system_prompt):
    client = _get_gemini_client()
    if not client:
        return None

    try:
        import google.generativeai as genai

        model = genai.GenerativeModel(
            'gemini-2.5-flash',
            system_instruction=system_prompt
        )

        chat_history = []
        for msg in messages[:-1]:
            role = 'user' if msg['role'] == 'user' else 'model'
            chat_history.append({'role': role, 'parts': [msg['content']]})

        chat = model.start_chat(history=chat_history)
        response = chat.send_message(messages[-1]['content'])
        return response.text
    except Exception:
        return None


def find_matching_jobs(student_profile, resumes=None):
    from DRF.myapp.models import Job, Resume

    profile_data, category_keywords = _build_user_profile(student_profile)
    existing_skills = set()
    if resumes:
        for resume in resumes:
            existing_skills.update(resume.skills or [])

    top_categories = sorted(category_keywords.items(), key=lambda x: x[1], reverse=True)[:3]
    preferred_category_slugs = [slug for slug, _ in top_categories]

    jobs = Job.objects.filter(is_active=True).select_related('employer', 'category')

    scored_jobs = []
    for job in jobs:
        score = 0

        if job.category and job.category.slug in preferred_category_slugs:
            idx = preferred_category_slugs.index(job.category.slug)
            score += (3 - idx) * 30

        job_text = f"{job.title} {job.description}".lower()

        skill_matches = 0
        for skill in existing_skills:
            if skill.lower() in job_text:
                skill_matches += 1
        score += skill_matches * 15

        job_skills = _extract_job_skills(job_text)
        for js in job_skills:
            for es in existing_skills:
                if js.lower() == es.lower():
                    score += 10

        if not job.experience_required:
            score += 10

        schedule_compat = {
            'flexible': ['flexible', 'part_time'],
            'part_time': ['flexible', 'part_time'],
            'full_time': ['flexible', 'part_time', 'full_time'],
        }
        student_pref = profile_data.get('course', 3)
        if student_pref and student_pref <= 2 and job.schedule == 'full_time':
            score -= 10

        if score > 0:
            scored_jobs.append((score, job))

    scored_jobs.sort(key=lambda x: x[0], reverse=True)
    return scored_jobs[:20]


def _extract_job_skills(text):
    common_skills = [
        'python', 'javascript', 'typescript', 'java', 'c++', 'go', 'rust', 'php', 'swift', 'kotlin',
        'react', 'vue', 'angular', 'node.js', 'django', 'flask', 'fastapi', 'spring',
        'sql', 'postgresql', 'mysql', 'mongodb', 'redis',
        'docker', 'kubernetes', 'aws', 'git', 'linux', 'ci/cd',
        'figma', 'photoshop', 'illustrator', 'sketch',
        'excel', 'power bi', 'tableau',
        'seo', 'google ads', 'yandex direct', 'analytics',
        'agile', 'scrum', 'kanban', 'jira',
        'html', 'css', 'sass', 'tailwind',
        'rest api', 'graphql', 'grpc',
    ]
    found = []
    for skill in common_skills:
        if skill in text:
            found.append(skill)
    return found