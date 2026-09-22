import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import re
import json
from django.utils import timezone
from datetime import datetime
from django.contrib.auth import get_user_model
from .models import Job, Category, EmployerProfile

User = get_user_model()


class SomonTjParser:
    BASE_URL = 'https://somon.tj'
    JOBS_URL = 'https://somon.tj/vakansii/'

    CATEGORY_MAPPING = {
        'it': 'Программирование',
        'programming': 'Программирование',
        'design': 'Дизайн',
        'marketing': 'Маркетинг',
        'sales': 'Продажи',
        'finance': 'Финансы',
        'admin': 'Администрирование',
        'hr': 'HR',
        'engineering': 'Инженерия',
        'education': 'Образование',
        'medicine': 'Медицина',
        'construction': 'Строительство',
        'transport': 'Транспорт',
        'hospitality': 'Гостиницы/Рестораны',
        'beauty': 'Красота/Спорт',
        'media': 'Медиа/Искусство',
        'legal': 'Юриспруденция',
        'agriculture': 'Сельское хозяйство',
        'manufacturing': 'Производство',
        'retail': 'Ритейл',
        'security': 'Безопасность',
        'other': 'Другое',
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        })

    def get_category(self, slug_or_name):
        slug_or_name = slug_or_name.lower().strip()
        for key, name in self.CATEGORY_MAPPING.items():
            if key in slug_or_name or name.lower() in slug_or_name:
                category, _ = Category.objects.get_or_create(
                    name=name,
                    defaults={'slug': key}
                )
                return category
        category, _ = Category.objects.get_or_create(
            name='Другое',
            defaults={'slug': 'other'}
        )
        return category

    def parse_salary(self, text):
        if not text:
            return None, None
        text = text.replace(' ', '').replace('\xa0', '').replace('c.', '')
        numbers = re.findall(r'\d+', text)
        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])
        elif len(numbers) == 1:
            val = int(numbers[0])
            return val, val
        return None, None

    def parse_schedule(self, text):
        if not text:
            return 'flexible'
        text = text.lower()
        if 'полн' in text or 'full' in text:
            return 'full_time'
        if 'частич' in text or 'part' in text or '2-4' in text or '2–4' in text:
            return 'part_time'
        return 'flexible'

    def parse_work_format(self, text):
        if not text:
            return 'offline'
        text = text.lower()
        if 'удал' in text or 'remote' in text or 'онлайн' in text:
            return 'online'
        if 'гибрид' in text or 'hybrid' in text:
            return 'hybrid'
        return 'offline'

    def fetch_page(self, url):
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def parse_job_list(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        jobs = []

        # somon.tj uses schema.org/JobPosting structured data on cards
        cards = soup.find_all('div', attrs={'itemtype': 'http://schema.org/JobPosting'})
        print(f"Found {len(cards)} vacancy cards")

        for card in cards:
            try:
                # Title from meta itemprop="title"
                title_meta = card.find('meta', itemprop='title')
                title = title_meta['content'] if title_meta else ''

                # Description from meta itemprop="description"
                desc_meta = card.find('meta', itemprop='description')
                description = desc_meta['content'] if desc_meta else ''

                # Link
                link = card.find('a', href=True)
                if not link:
                    continue
                job_url = urljoin(self.BASE_URL, link['href'])
                job_id = self.extract_job_id(job_url)

                # Salary: span with font-medium + text-base
                salary_span = card.find('span', class_=lambda c: c and 'font-medium' in c and 'text-base' in c)
                salary_text = salary_span.get_text(strip=True) if salary_span else ''

                # Company: span with font-bold + text-sm (exclude VIP/ТОП badges)
                company = ''
                for span in card.find_all('span'):
                    classes = ' '.join(span.get('class', []))
                    text = span.get_text(strip=True)
                    if 'font-bold' in classes and 'text-sm' in classes and 'bg-' not in classes:
                        if text and text not in ('VIP', 'ТОП', 'VIN'):
                            company = text
                            break

                # Location: last p with muted-foreground (contains time + city)
                location = ''
                muted_ps = card.find_all('p', class_=lambda c: c and 'muted-foreground' in c)
                if muted_ps:
                    loc_text = muted_ps[-1].get_text(strip=True)
                    # Remove time prefix like "X минут назад", "1 час назад", "2 дня назад"
                    # Pattern: [number] [минут/час/день/дней] назад
                    clean_text = re.sub(r'\d+\s*(?:минут|час|день|дней?)\s*назад\s*', '', loc_text)
                    # Also remove any leading whitespace that might remain
                    location = clean_text.strip()

                if title and len(title) > 2:
                    jobs.append({
                        'source_id': job_id,
                        'source_url': job_url,
                        'title': title,
                        'description': description,
                        'company': company,
                        'salary_text': salary_text,
                        'location': location,
                    })
            except Exception as e:
                print(f"Error parsing job item: {e}")
                continue

        return jobs

    def extract_job_id(self, url):
        match = re.search(r'/adv/(\d+)', url)
        if match:
            return match.group(1)
        match = re.search(r'/(\d+)', url)
        return match.group(1) if match else ''

    def parse_job_detail(self, html, job_data):
        soup = BeautifulSoup(html, 'html.parser')

        # Try to get structured data from JSON-LD (most reliable)
        ld_data = self._extract_jsonld(soup)

        if ld_data:
            return self._parse_from_jsonld(ld_data, job_data)

        # Fallback to HTML parsing
        return self._parse_from_html(soup, job_data)

    def _extract_jsonld(self, soup):
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and '@graph' in data:
                    for item in data['@graph']:
                        if item.get('@type') == 'JobPosting':
                            return item
                elif isinstance(data, dict) and data.get('@type') == 'JobPosting':
                    return data
            except (json.JSONDecodeError, AttributeError):
                continue
        return None

    def _parse_from_jsonld(self, ld, job_data):
        description = ld.get('description', job_data.get('description', ''))

        salary_min, salary_max = None, None
        base_salary = ld.get('baseSalary', {})
        if base_salary and isinstance(base_salary, dict):
            value = base_salary.get('value', {})
            if isinstance(value, dict):
                salary_val = value.get('value')
                if salary_val:
                    salary_min = int(salary_val)
                    salary_max = int(salary_val)

        company = ''
        org = ld.get('hiringOrganization', {})
        if org and isinstance(org, dict):
            company = org.get('name', '')

        location = ''
        loc = ld.get('jobLocation', {})
        if loc and isinstance(loc, dict):
            addr = loc.get('address', {})
            if isinstance(addr, dict):
                city = addr.get('addressLocality', '')
                country = addr.get('addressCountry', '')
                location = f"{city}, {country}" if city else country

        schedule = self.parse_schedule(description)
        work_format = self.parse_work_format(description)
        experience_required = any(w in description.lower() for w in ['опыт', 'стаж', 'experience'])

        return {
            'description': description,
            'salary_min': salary_min,
            'salary_max': salary_max,
            'schedule': schedule,
            'work_format': work_format,
            'experience_required': experience_required,
            'location_address': location or job_data.get('location', ''),
            'company': company or job_data.get('company', ''),
        }

    def _parse_from_html(self, soup, job_data):
        desc_elem = soup.find(class_=re.compile(r'description|content|detail'))
        description = desc_elem.get_text(strip=True) if desc_elem else job_data.get('description', '')

        salary_min, salary_max = self.parse_salary(job_data.get('salary_text', ''))
        schedule = self.parse_schedule(description)
        work_format = self.parse_work_format(description)
        experience_required = any(w in description.lower() for w in ['опыт', 'стаж', 'experience'])

        return {
            'description': description,
            'salary_min': salary_min,
            'salary_max': salary_max,
            'schedule': schedule,
            'work_format': work_format,
            'experience_required': experience_required,
            'location_address': job_data.get('location', ''),
            'company': job_data.get('company', ''),
        }

    def get_or_create_employer(self, company_name):
        if not company_name:
            company_name = 'Не указана'

        user, user_created = User.objects.get_or_create(
            username=company_name[:30] or 'somon_parser',
            defaults={
                'email': f'parser@{company_name[:30]}.local',
                'role': 'employer',
                'is_active': True,
            }
        )

        employer, created = EmployerProfile.objects.get_or_create(
            user=user,
            company_name=company_name,
            defaults={
                'description': 'Автоматически импортировано из somon.tj',
                'address': '',
            }
        )
        return employer

    def save_job(self, job_data, detail_data):
        category = self.get_category(detail_data.get('description', '') + ' ' + job_data.get('title', ''))
        employer = self.get_or_create_employer(detail_data.get('company', ''))

        job, created = Job.objects.get_or_create(
            source='somon_tj',
            source_id=job_data['source_id'],
            defaults={
                'employer': employer,
                'category': category,
                'title': job_data['title'],
                'description': detail_data.get('description', ''),
                'salary_min': detail_data.get('salary_min'),
                'salary_max': detail_data.get('salary_max'),
                'schedule': detail_data.get('schedule', 'flexible'),
                'work_format': detail_data.get('work_format', 'offline'),
                'experience_required': detail_data.get('experience_required', False),
                'location_address': detail_data.get('location_address', ''),
                'source_url': job_data['source_url'],
                'is_active': True,
            }
        )

        if not created:
            job.title = job_data['title']
            job.description = detail_data.get('description', '')
            job.salary_min = detail_data.get('salary_min')
            job.salary_max = detail_data.get('salary_max')
            job.schedule = detail_data.get('schedule', 'flexible')
            job.work_format = detail_data.get('work_format', 'offline')
            job.experience_required = detail_data.get('experience_required', False)
            job.location_address = detail_data.get('location_address', '')
            job.is_active = True
            job.save()

        return job, created

    def parse_and_save(self, max_jobs=20):
        print(f"Starting parsing from somon.tj/vakansii/...")
        html = self.fetch_page(self.JOBS_URL)
        if not html:
            return {'success': False, 'error': 'Failed to fetch main page'}

        jobs_list = self.parse_job_list(html)
        print(f"Found {len(jobs_list)} jobs on list page")

        results = {'created': 0, 'updated': 0, 'errors': 0}

        for i, job_data in enumerate(jobs_list[:max_jobs]):
            try:
                print(f"Parsing job {i+1}/{min(len(jobs_list), max_jobs)}: {job_data['title'][:50]}")

                detail_html = self.fetch_page(job_data['source_url'])
                if not detail_html:
                    results['errors'] += 1
                    continue

                detail_data = self.parse_job_detail(detail_html, job_data)
                job, created = self.save_job(job_data, detail_data)
                if created:
                    results['created'] += 1
                else:
                    results['updated'] += 1

                time.sleep(1)

            except Exception as e:
                print(f"Error processing job: {e}")
                results['errors'] += 1

        print(f"Parsing completed: {results}")
        return {'success': True, **results}


def parse_somon_tj_jobs(max_jobs=20):
    parser = SomonTjParser()
    return parser.parse_and_save(max_jobs)
