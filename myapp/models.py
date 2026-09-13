import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Студент'),
        ('employer', 'Работодатель'),
        ('admin', 'Администратор'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    location = models.CharField(max_length=200, blank=True)
    is_email_verified = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'


class EmailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verifications')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Верификация email'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} - {self.token}'


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Токены сброса пароля'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} - {self.token}'


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    university = models.CharField(max_length=200, blank=True)
    faculty = models.CharField(max_length=200, blank=True)
    course = models.PositiveIntegerField(blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f'Профиль: {self.user.username}'


class EmployerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employer_profile')
    company_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    address = models.CharField(max_length=300, blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.company_name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class WorkSchedule(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'Графики работы'
        ordering = ['name']

    def __str__(self):
        return self.name


class WorkFormat(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'Форматы работы'
        ordering = ['name']

    def __str__(self):
        return self.name


class WorkExperience(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'Опыт работы'
        ordering = ['name']

    def __str__(self):
        return self.name


class Resume(models.Model):
    SCHEDULE_CHOICES = (
        ('flexible', 'Гибкий'),
        ('part_time', '2-4 часа'),
        ('full_time', 'Полная занятость'),
    )
    FORMAT_CHOICES = (
        ('online', 'Онлайн'),
        ('offline', 'Офлайн'),
        ('hybrid', 'Гибрид'),
    )
    STYLE_CHOICES = (
        ('classic', 'Классический'),
        ('modern', 'Современный'),
        ('minimal', 'Минималистичный'),
        ('creative', 'Креативный'),
    )
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='resumes')
    title = models.CharField(max_length=200, verbose_name='Желаемая должность')
    about = models.TextField(blank=True, verbose_name='О себе')
    skills = models.JSONField(default=list, blank=True, verbose_name='Навыки')
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_CHOICES, default='flexible')
    work_format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='online')
    schedule = models.ForeignKey(WorkSchedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='resumes', verbose_name='График работы')
    format = models.ForeignKey(WorkFormat, on_delete=models.SET_NULL, null=True, blank=True, related_name='resumes', verbose_name='Формат работы')
    github_url = models.URLField(max_length=300, blank=True, null=True, verbose_name='GitHub')
    portfolio_url = models.URLField(max_length=300, blank=True, null=True, verbose_name='Портфолио')
    linkedin_url = models.URLField(max_length=300, blank=True, null=True, verbose_name='LinkedIn')
    style = models.CharField(max_length=20, choices=STYLE_CHOICES, default='modern', verbose_name='Стиль резюме')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Резюме'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.student.user.username}'


class Job(models.Model):
    SCHEDULE_CHOICES = (
        ('flexible', 'Гибкий'),
        ('part_time', '2-4 часа'),
        ('full_time', 'Полная занятость'),
    )
    FORMAT_CHOICES = (
        ('online', 'Онлайн'),
        ('offline', 'Офлайн'),
        ('hybrid', 'Гибрид'),
    )
    SOURCE_CHOICES = (
        ('manual', 'Ручное'),
        ('somon_tj', 'somon.tj'),
    )
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name='jobs')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='jobs')
    title = models.CharField(max_length=200)
    description = models.TextField()
    salary_min = models.PositiveIntegerField(blank=True, null=True)
    salary_max = models.PositiveIntegerField(blank=True, null=True)
    min_age = models.PositiveIntegerField(default=16)
    schedule = models.CharField(max_length=20, choices=SCHEDULE_CHOICES, default='flexible')
    work_format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='online')
    experience_required = models.BooleanField(default=False)
    work_schedule = models.ForeignKey(WorkSchedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs', verbose_name='График работы')
    work_format_fk = models.ForeignKey(WorkFormat, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs', verbose_name='Формат работы')
    experience = models.ForeignKey(WorkExperience, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs', verbose_name='Опыт работы')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    image = models.ImageField(upload_to='jobs/', blank=True, null=True, verbose_name='Изображение вакансии')
    location_lat = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, verbose_name='Широта')
    location_lng = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, verbose_name='Долгота')
    location_address = models.CharField(max_length=300, blank=True, verbose_name='Адрес на карте')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual', verbose_name='Источник')
    source_url = models.URLField(blank=True, verbose_name='Ссылка на источник')
    source_id = models.CharField(max_length=100, blank=True, verbose_name='ID в источнике')

    class Meta:
        verbose_name_plural = 'Вакансии'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def has_location(self):
        return self.location_lat is not None and self.location_lng is not None


class Application(models.Model):
    STATUS_CHOICES = (
        ('sent', 'Отправлено'),
        ('viewed', 'Просмотрено'),
        ('interview', 'Собеседование'),
        ('accepted', 'Принято'),
        ('rejected', 'Отклонено'),
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    cover_letter = models.TextField(blank=True, verbose_name='Сопроводительное письмо')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Отклики'
        ordering = ['-created_at']
        unique_together = ['job', 'resume']

    def __str__(self):
        return f'{self.resume.student.user.username} -> {self.job.title}'


class Favorite(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='favorites')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Избранное'
        ordering = ['-created_at']
        unique_together = ['student', 'job']

    def __str__(self):
        return f'{self.student.user.username} - {self.job.title}'


class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions', null=True, blank=True)
    title = models.CharField(max_length=200, default='Новый чат')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Чат сессии'
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.title} - {self.user.username}'


class ChatMessage(models.Model):
    ROLE_CHOICES = (
        ('user', 'Пользователь'),
        ('assistant', 'Ассистент'),
    )
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Сообщения чата'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.role}: {self.content[:50]}'


class DirectMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Личные сообщения'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender.username} -> {self.recipient.username}: {self.content[:50]}'


class Notification(models.Model):
    TYPE_CHOICES = (
        ('application_viewed', 'Отлик просмотрен'),
        ('application_accepted', 'Отлик принят'),
        ('application_rejected', 'Отлик отклонён'),
        ('application_interview', 'Приглашение на собеседование'),
        ('message', 'Сообщение'),
        ('system', 'Системное'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='system')
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    link = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username}: {self.title}'