import os
import requests as http_requests
from django.conf import settings
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.http import FileResponse, HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Max
from .models import (
    StudentProfile, EmployerProfile,
    Category, Resume, Job, Application, Favorite,
    ChatSession, ChatMessage, EmailVerification, DirectMessage,
    WorkSchedule, WorkFormat, WorkExperience, Notification,
    TariffPlan, UserSubscription, Payment
)
from .serializers import (
    UserSerializer, UserRegisterSerializer,
    StudentProfileSerializer, EmployerProfileSerializer,
    CategorySerializer, CategoryWithCountSerializer,
    ResumeSerializer, ResumeCreateSerializer,
    JobSerializer, JobCreateSerializer,
    ApplicationSerializer, ApplicationCreateSerializer,
    FavoriteSerializer,
    ChatSessionSerializer, ChatSessionListSerializer, ChatMessageSerializer,
    DirectMessageSerializer,
    WorkScheduleSerializer, WorkFormatSerializer, WorkExperienceSerializer,
    NotificationSerializer,
    TariffPlanSerializer, UserSubscriptionSerializer, PaymentSerializer, CreatePaymentSerializer,
)
from .permissions import IsOwnerOrReadOnly, IsEmployer, IsStudent, IsAdminRole

User = get_user_model()

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:8000/api/auth/google/callback/')


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()
        conversation_user_ids = DirectMessage.objects.filter(
            Q(sender=self.request.user) | Q(recipient=self.request.user)
        ).values_list('sender', 'recipient')
        user_ids = set()
        for sender_id, recipient_id in conversation_user_ids:
            user_ids.add(sender_id)
            user_ids.add(recipient_id)
        user_ids.add(self.request.user.id)
        return User.objects.filter(id__in=user_ids)

    @action(detail=False, methods=['get', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        if request.method == 'PATCH':
            serializer = UserSerializer(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class StudentProfileViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.role == 'student':
            return StudentProfile.objects.filter(user=self.request.user)
        return StudentProfile.objects.all()

    def perform_update(self, serializer):
        if serializer.instance.user != self.request.user:
            self.permission_denied(self.request)
        serializer.save()


class EmployerProfileViewSet(viewsets.ModelViewSet):
    queryset = EmployerProfile.objects.all()
    serializer_class = EmployerProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.role == 'employer':
            return EmployerProfile.objects.filter(user=self.request.user)
        return EmployerProfile.objects.all()

    def perform_update(self, serializer):
        if serializer.instance.user != self.request.user:
            self.permission_denied(self.request)
        serializer.save()


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminRole()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.action == 'list':
            return CategoryWithCountSerializer
        return CategorySerializer


class WorkScheduleViewSet(viewsets.ModelViewSet):
    queryset = WorkSchedule.objects.all()
    serializer_class = WorkScheduleSerializer
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminRole()]
        return [permissions.AllowAny()]


class WorkFormatViewSet(viewsets.ModelViewSet):
    queryset = WorkFormat.objects.all()
    serializer_class = WorkFormatSerializer
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminRole()]
        return [permissions.AllowAny()]


class WorkExperienceViewSet(viewsets.ModelViewSet):
    queryset = WorkExperience.objects.all()
    serializer_class = WorkExperienceSerializer
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminRole()]
        return [permissions.AllowAny()]


class ResumeViewSet(viewsets.ModelViewSet):
    queryset = Resume.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['schedule_type', 'work_format']
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ResumeCreateSerializer
        return ResumeSerializer

    def get_queryset(self):
        qs = Resume.objects.all()
        if self.request.user.is_authenticated and self.request.user.role == 'student':
            try:
                return qs.filter(student=self.request.user.student_profile)
            except StudentProfile.DoesNotExist:
                return qs.none()
        return qs

    def perform_create(self, serializer):
        try:
            serializer.save(student=self.request.user.student_profile)
        except StudentProfile.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Профиль студента не найден. Заполните профиль.')

    def perform_update(self, serializer):
        if serializer.instance.student.user != self.request.user:
            self.permission_denied(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        if instance.student.user != self.request.user:
            self.permission_denied(self.request)
        instance.delete()


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'schedule', 'work_format', 'min_age']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'salary_min', 'salary_max']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsEmployer()]

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return JobCreateSerializer
        return JobSerializer

    def get_queryset(self):
        qs = Job.objects.annotate(
            applications_count=Count('applications'),
        )
        if self.request.user.is_authenticated and self.request.user.role == 'employer':
            try:
                return qs.filter(employer=self.request.user.employer_profile)
            except EmployerProfile.DoesNotExist:
                return qs.none()
        return qs.filter(is_active=True)

    def perform_create(self, serializer):
        try:
            serializer.save(employer=self.request.user.employer_profile)
        except EmployerProfile.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Профиль работодателя не найден. Заполните профиль.')

    def perform_update(self, serializer):
        if serializer.instance.employer.user != self.request.user:
            self.permission_denied(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        if instance.employer.user != self.request.user:
            self.permission_denied(self.request)
        instance.delete()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def toggle_active(self, request, pk=None):
        job = self.get_object()
        if job.employer.user != request.user:
            return Response({'detail': 'Нет прав.'}, status=status.HTTP_403_FORBIDDEN)
        job.is_active = not job.is_active
        job.save()
        return Response({'is_active': job.is_active})

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def mine(self, request):
        if request.user.role != 'employer':
            return Response({'detail': 'Только для работодателей.'}, status=status.HTTP_403_FORBIDDEN)
        jobs = Job.objects.filter(employer=request.user.employer_profile).annotate(
            applications_count=Count('applications'),
        )
        page = self.paginate_queryset(jobs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(jobs, many=True)
        return Response(serializer.data)


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ('create',):
            return ApplicationCreateSerializer
        return ApplicationSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Application.objects.none()
        if self.request.user.role == 'student':
            try:
                return Application.objects.filter(resume__student=self.request.user.student_profile)
            except StudentProfile.DoesNotExist:
                return Application.objects.none()
        elif self.request.user.role == 'employer':
            try:
                return Application.objects.filter(job__employer=self.request.user.employer_profile)
            except EmployerProfile.DoesNotExist:
                return Application.objects.none()
        return Application.objects.none()

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'], permission_classes=[IsEmployer])
    def update_status(self, request, pk=None):
        application = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(Application.STATUS_CHOICES):
            return Response({'detail': 'Неверный статус.'}, status=status.HTTP_400_BAD_REQUEST)
        old_status = application.status
        application.status = new_status
        application.save()

        if old_status != new_status:
            student_user = application.resume.student.user
            job_title = application.job.title
            company_name = application.job.employer.company_name
            notification_link = f'/applications/{application.id}'

            status_messages = {
                'viewed': f'Ваш отлик на вакансию «{job_title}» компании «{company_name}» просмотрен.',
                'rejected': f'Ваш отлик на вакансию «{job_title}» компании «{company_name}» отклонён.',
                'accepted': f'Ваш отлик на вакансию «{job_title}» компании «{company_name}» принят!',
                'interview': f'Вас пригласили на собеседование по вакансии «{job_title}» компании «{company_name}».',
            }

            if new_status in status_messages:
                Notification.objects.create(
                    user=student_user,
                    notification_type=f'application_{new_status}',
                    title=f'Отлик на «{job_title}»',
                    message=status_messages[new_status],
                    link=notification_link,
                )

                try:
                    from channels.layers import get_channel_layer
                    from asgiref.sync import async_to_sync
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f'user_{student_user.id}',
                        {
                            'type': 'send_notification',
                            'notification_type': f'application_{new_status}',
                            'title': f'Отлик на «{job_title}»',
                            'message': status_messages[new_status],
                            'data': {'link': notification_link},
                        }
                    )
                except Exception:
                    pass

        return Response(ApplicationSerializer(application).data)


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Favorite.objects.none()
        try:
            return Favorite.objects.filter(student=self.request.user.student_profile)
        except StudentProfile.DoesNotExist:
            return Favorite.objects.none()

    def perform_create(self, serializer):
        try:
            serializer.save(student=self.request.user.student_profile)
        except StudentProfile.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Профиль студента не найден.')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_to_favorites(request):
    if request.user.role != 'student':
        return Response({'detail': 'Только для студентов.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        student_profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return Response({'detail': 'Профиль студента не найден.'}, status=status.HTTP_404_NOT_FOUND)
    job_id = request.data.get('job_id')
    if not job_id:
        return Response({'detail': 'job_id обязателен.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return Response({'detail': 'Вакансия не найдена.'}, status=status.HTTP_404_NOT_FOUND)
    fav, created = Favorite.objects.get_or_create(
        student=student_profile, job=job
    )
    if not created:
        return Response({'detail': 'Уже в избранном.'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': 'Добавлено в избранное.', 'id': fav.id}, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def remove_from_favorites(request, job_id):
    try:
        student_profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return Response({'detail': 'Профиль студента не найден.'}, status=status.HTTP_404_NOT_FOUND)
    try:
        fav = Favorite.objects.get(student=student_profile, job_id=job_id)
        fav.delete()
        return Response({'detail': 'Удалено из избранного.'})
    except Favorite.DoesNotExist:
        return Response({'detail': 'Не найдено.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def ai_generate_resume(request):
    if request.user.role != 'student':
        return Response({'detail': 'Только для студентов.'}, status=status.HTTP_403_FORBIDDEN)

    from .ai_service import generate_resume

    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return Response({'detail': 'Профиль студента не найден. Заполните профиль.'}, status=status.HTTP_404_NOT_FOUND)

    result = generate_resume(profile)
    return Response(result)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def ai_create_resume(request):
    if request.user.role != 'student':
        return Response({'detail': 'Только для студентов.'}, status=status.HTTP_403_FORBIDDEN)

    from .ai_service import generate_resume

    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return Response({'detail': 'Профиль студента не найден. Заполните профиль.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        result = generate_resume(profile)
    except Exception:
        return Response({'detail': 'Ошибка генерации резюме.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    resume = Resume.objects.create(
        student=profile,
        title=result.get('title', 'Резюме'),
        about=result.get('about', ''),
        skills=result.get('skills', []),
        schedule_type=result.get('schedule_type', 'flexible'),
        work_format=result.get('work_format', 'online'),
    )

    serializer = ResumeSerializer(resume)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


RESUME_CHAT_SYSTEM_PROMPT = """Ты — карьерный консультант, который помогает студенту составить резюме.

Твоя задача: задавать пользователю вопросы по очереди, чтобы собрать информацию для резюме.

ПОРЯДОК ВОПРОСОВ (по одному за раз):
1. "На какую должность вы претендуете?"
2. "Какие у вас навыки? (технологии, инструменты, языки программирования)"
3. "Расскажите о вашем опыте — были ли стажировки, проекты, хакатоны?"
4. "Какой график вам подходит? (гибкий, 2-4 часа, полная занятость)"
5. "Какой формат работы предпочитаете? (онлайн, офлайн, гибрид)"

ЖЁСТКИЕ ПРАВИЛА:
- Пока не получен ответ на ВСЕ 5 вопросов выше — отвечай ТОЛЬКО обычным текстом со следующим вопросом. НЕ включай JSON, блоки кода и не пиши, что резюме готово.
- Ответ — это либо ОДИН вопрос, либо финальный результат. Никогда не смешивай вопрос и JSON в одном сообщении.
- Не выдумывай навыки и опыт за пользователя — жди его ответов.
- Когда все данные собраны, ответь сначала коротким текстом ("Резюме готово! Нажмите кнопку 'Сохранить'.") и затем СТРОГО блоком:
```resume
{
  "title": "желаемая должность",
  "about": "текст 'О себе' (3-5 предложений)",
  "skills": ["навык1", "навык2", ...],
  "schedule_type": "flexible" или "part_time" или "full_time",
  "work_format": "online" или "offline" или "hybrid"
}
```
- После блока ```resume не задавай никаких вопросов — диалог завершён.

НОСИТЕЛЬЯ ДАННЫХ СТУДЕНТА (уже известны, НЕ спрашивай):
- Университет, факультет, курс, город, имя

Стиль общения: дружелюбный, профессиональный. Отвечай на языке пользователя."""


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def ai_resume_chat(request):
    if request.user.role != 'student':
        return Response({'detail': 'Только для студентов.'}, status=status.HTTP_403_FORBIDDEN)

    message = request.data.get('message', '').strip()
    history = request.data.get('history', [])

    if not message:
        return Response({'detail': 'Сообщение обязательно.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        profile = request.user.student_profile
        student_context = f"\nДАННЫЕ СТУДЕНТА: {request.user.username}, {profile.university or ''}, {profile.faculty or ''}, {profile.course or ''} курс, {profile.city or ''}."
    except StudentProfile.DoesNotExist:
        student_context = ""

    system_prompt = RESUME_CHAT_SYSTEM_PROMPT + student_context

    from .ai_service import _chat_with_gemini

    all_messages = history + [{'role': 'user', 'content': message}]
    ai_response = _chat_with_gemini(all_messages, system_prompt)

    if not ai_response:
        ai_response = "Извините, произошла ошибка. Попробуйте ещё раз."

    import json as _json
    resume_data = None
    try:
        text = ai_response.strip()
        block = None
        if '```resume' in text:
            block = text.split('```resume', 1)[1].rsplit('```', 1)[0].strip()
        else:
            candidate = text
            if '```json' in candidate:
                candidate = candidate.split('```json', 1)[1].rsplit('```', 1)[0].strip()
            elif '```' in candidate:
                candidate = candidate.split('```', 1)[1].rsplit('```', 1)[0].strip()
            if candidate.startswith('{') and candidate.endswith('}'):
                block = candidate
        if block:
            data = _json.loads(block)
            if (
                isinstance(data, dict)
                and str(data.get('title') or '').strip()
                and isinstance(data.get('skills'), list)
                and data.get('skills')
                and data.get('schedule_type')
                and data.get('work_format')
            ):
                resume_data = data
    except Exception:
        resume_data = None

    message = ai_response
    if resume_data is not None:
        cleaned = message
        if '```resume' in cleaned:
            start = cleaned.find('```resume')
            after = cleaned[start + len('```resume'):]
            close = after.find('```')
            cleaned = (cleaned[:start] + (after[close + 3:] if close != -1 else '')).strip()
        elif cleaned.startswith('{') and cleaned.endswith('}'):
            cleaned = ''
        message = cleaned or 'Резюме готово! Нажмите кнопку "Сохранить".'

    return Response({
        'message': message,
        'resume_data': resume_data,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def ai_recommend_jobs(request):
    if request.user.role != 'student':
        return Response({'detail': 'Только для студентов.'}, status=status.HTTP_403_FORBIDDEN)

    from .ai_service import find_matching_jobs

    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return Response({'detail': 'Профиль студента не найден. Заполните профиль.'}, status=status.HTTP_404_NOT_FOUND)

    resumes = Resume.objects.filter(student=profile)
    scored_jobs = find_matching_jobs(profile, resumes)

    results = []
    for score, job in scored_jobs:
        job_data = JobSerializer(job, context={'request': request}).data
        job_data['match_score'] = min(score, 100)
        results.append(job_data)

    return Response(results)


class ChatSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return ChatSessionListSerializer
        return ChatSessionSerializer

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.user != self.request.user:
            self.permission_denied(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            self.permission_denied(self.request)
        instance.delete()


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def chat_send_message(request):
    session_id = request.data.get('session_id')
    message_content = request.data.get('message', '').strip()

    if not message_content:
        return Response({'detail': 'Сообщение обязательно.'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user if request.user.is_authenticated else None

    if session_id:
        try:
            if user:
                session = ChatSession.objects.get(id=session_id, user=user)
            else:
                session = ChatSession.objects.get(id=session_id, user__isnull=True)
        except ChatSession.DoesNotExist:
            return Response({'detail': 'Сессия не найдена.'}, status=status.HTTP_404_NOT_FOUND)
    else:
        title = message_content[:50] + ('...' if len(message_content) > 50 else '')
        session = ChatSession.objects.create(user=user, title=title)

    ChatMessage.objects.create(session=session, role='user', content=message_content)

    messages = list(session.messages.order_by('created_at').values('role', 'content'))

    student_context = ""
    if user and user.role == 'student':
        try:
            profile = user.student_profile
            parts = []
            if profile.university:
                parts.append(f"- Университет: {profile.university}")
            if profile.faculty:
                parts.append(f"- Факультет: {profile.faculty}")
            if profile.course:
                parts.append(f"- Курс: {profile.course}")
            if profile.city:
                parts.append(f"- Город: {profile.city}")
            if parts:
                student_context = "\n\nДАННЫЕ СТУДЕНТА ИЗ ЕГО ПРОФИЛЯ (уже заполнены, НЕ спрашивай это):\n" + "\n".join(parts)
        except StudentProfile.DoesNotExist:
            pass

    system_prompt = f"""Ты — карьерный консультант и помощник для студентов и работодателей платформы CareerHub.

Твоя РОЛЬ — помогать ТОЛЬКО с карьерными вопросами:
- Создание и улучшение резюме
- Поиск работы и стажировок
- Подготовка к собеседованиям
- Советы по карьерному развитию
- Вопросы о работе, вакансиях, навыках, зарплате, графике

СТРОГИЕ ПРАВИЛА:
1. ТЫ ОБЯЗАН ОТВЕЧАТЬ ТОЛЬКО НА ВОПРОСЫ, СВЯЗАННЫЕ С КАРЬЕРОЙ, РАБОТОЙ, ОБУЧЕНИЕМ, НАВЫКАМИ, РЕЗЮМЕ, ВАКАНСИЯМИ, СОБЕСЕДОВАНИЯМИ.
2. ЕСЛИ ПОЛЬЗОВАТЕЛЬ СПРАШИВАЕТ О ЧЁМ-ТО НЕ СВЯЗАННОМ С КАРЬЕРОЙ (погода, рецепты, фильмы, политика, личная жизнь, математика и т.д.) — ВЕЖЛИВО ОТКАЖИ И НАПОМНИ О СВОЁЙ РОЛИ. Пример: "Извините, я помогаю только с карьерными вопросами. Могу помочь с резюме, поиском работы или подготовкой к собеседованию."
3. НИКОГДА не повторяй одно и то же предложение. Каждый ответ должен быть уникальным и适应 контексту.
4. Сначала ЗАДАВАЙ уточняющие вопросы (2-3 за раз), чтобы понять ситуацию.
5. НЕ спрашивай то, что уже известно из данных студента ниже.
6. Только ПОСЛЕ получения полной информации — давай рекомендации.
7. Отвечай на языке пользователя.{student_context}

Формат ответа: кратко, по делу, с конкретными建议. Не перегружай пользователя."""

    from .ai_service import _chat_with_gemini

    all_messages = messages if messages else [{'role': 'user', 'content': message_content}]
    ai_response = _chat_with_gemini(all_messages, system_prompt)
    if not ai_response:
        ai_response = _fallback_ai_response(message_content, user)

    ChatMessage.objects.create(session=session, role='assistant', content=ai_response)

    session.save()

    return Response({
        'session_id': session.id,
        'session_title': session.title,
        'user_message': {'role': 'user', 'content': message_content},
        'assistant_message': {'role': 'assistant', 'content': ai_response},
    })


def _fallback_ai_response(message, user=None):
    import random
    message_lower = message.lower()

    student_info = ""
    if user and hasattr(user, 'role') and user.role == 'student':
        try:
            profile = user.student_profile
            parts = []
            if profile.university:
                parts.append(f"Университет: {profile.university}")
            if profile.faculty:
                parts.append(f"Факультет: {profile.faculty}")
            if profile.course:
                parts.append(f"Курс: {profile.course}")
            if profile.city:
                parts.append(f"Город: {profile.city}")
            if parts:
                student_info = "\n\nИзвестные данные: " + "; ".join(parts) + "."
        except Exception:
            pass

    non_career_words = [
        'погода', 'рецепт', 'приготов', 'фильм', 'сериал', 'музыка', 'песн',
        'политика', 'президент', 'выбор', 'спорт', 'футбол', 'матч',
        'математик', 'сколько будет', 'посчитай', 'задач',
        'расскажи анекдот', 'шутк', 'юмор', 'привет как дела', 'как ты',
        'кто ты', 'что ты умеешь', 'смысл жизни', 'любовь', 'отношени',
        'кулинар', 'еда', 'ресторан', 'путешестви', 'отдых', 'тур',
        'здоровь', 'болит', 'лекарств', 'врач',
    ]
    
    if any(w in message_lower for w in non_career_words):
        refusals = [
            f"Извините, я помогаю только с карьерными вопросами.{student_info} Могу помочь с резюме, поиском работы или подготовкой к собеседованию.",
            f"Я карьерный консультант и специализируюсь на вопросах работы и карьеры.{student_info} Задайте вопрос о резюме, вакансиях или собеседовании.",
            f"Моя экспертиза — помощь в трудоустройстве и карьерном развитии.{student_info} Чем могу помочь в этой области?",
        ]
        return random.choice(refusals)

    if any(w in message_lower for w in ['резюме', 'cv', 'resume']):
        variants = [
            f"Давайте создадим отличное резюме!{student_info} Расскажите: какой опыт работы есть? Какими навыками владеете? На какую позицию претендуете?",
            f"Хорошо, поможем с резюме!{student_info} Мне нужно узнать: были ли стажировки? Какие технологии знаете? Какую должность ищете?",
            f"Отличная идея — начать с резюме!{student_info} Подскажите: есть ли опыт? Какие ключевые навыки? Куда хотите устроиться?",
        ]
        return random.choice(variants)
    
    elif any(w in message_lower for w in ['собеседование', 'interview', 'собеседовани']):
        variants = [
            f"Подготовимся к собеседованию!{student_info} На какую позицию? В какой компании? Какие вопросы вызывают трудности?",
            f"Отлично, давай подготовимся!{student_info} Расскажи: на какую должность? Какой формат собеседования (онлайн/офис)? Чего боишься больше всего?",
            f"С удовольствием помогу с подготовкой!{student_info} Какая позиция? Есть ли конкретные вопросы, которые беспокоят?",
        ]
        return random.choice(variants)
    
    elif any(w in message_lower for w in ['навык', 'skill', 'технологи']):
        variants = [
            f"Поможем определиться с навыками!{student_info} В какой сфере работаете? Какие технологии уже знаете? Какой формат работы предпочитаете?",
            f"Хороший вопрос!{student_info} Какая профессиональная область интересует? Есть ли уже какие-то навыки? Какой график удобен?",
            f"Давайте подберём нужные навыки!{student_info} Какую карьеру рассматриваете? Что уже умеете? Хотите удалёнку или офис?",
        ]
        return random.choice(variants)
    
    elif any(w in message_lower for w in ['ваканси', 'работ', 'job', 'vacancy']):
        variants = [
            f"Найдём подходящую работу!{student_info} В какой сфере ищете? Какая позиция интересна? Какой график предпочитаете?",
            f"Помогу с поиском вакансий!{student_info} Какая область? junior или стажировка? Удалённо или в офисе?",
            f"Отлично, давай подберём вакансии!{student_info} Какая специализация? Есть ли резюме? Какой график нужен?",
        ]
        return random.choice(variants)
    
    else:
        variants = [
            f"Привет! Я карьерный консультант.{student_info} Чем могу помочь? Резюме, поиск работы, подготовка к собеседованию?",
            f"Здравствуйте! Помогаю с карьерой.{student_info} Расскажите, что вас интересует — работу найти, резюме составить, или к собеседованию подготовиться?",
            f"Добро пожаловать! Я помогаю студентам с трудоустройством.{student_info} Задайте вопрос о работе, резюме или карьере.",
        ]
        return random.choice(variants)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def chat_session_messages(request, session_id):
    try:
        session = ChatSession.objects.get(id=session_id, user=request.user)
    except ChatSession.DoesNotExist:
        return Response({'detail': 'Сессия не найдена.'}, status=status.HTTP_404_NOT_FOUND)

    messages = session.messages.order_by('created_at')
    serializer = ChatMessageSerializer(messages, many=True)
    return Response({
        'session_id': session.id,
        'title': session.title,
        'messages': serializer.data,
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def send_verification_email(request):
    email = request.data.get('email')
    if not email:
        return Response({'detail': 'Email обязателен.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'detail': 'Пользователь с таким email не найден.'}, status=status.HTTP_404_NOT_FOUND)

    if user.is_email_verified:
        return Response({'detail': 'Email уже верифицирован.'}, status=status.HTTP_400_BAD_REQUEST)

    verification = EmailVerification.objects.create(user=user)

    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    verify_link = f"{frontend_url}/auth/verify-email?token={verification.token}"

    try:
        send_mail(
            subject='Верификация email - StudentJobs',
            message=f'Для верификации перейдите по ссылке: {verify_link}',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@studentjobs.com'),
            recipient_list=[email],
            fail_silently=False,
        )
        return Response({'detail': 'Письмо с ссылкой для верификации отправлено.'})
    except Exception as e:
        return Response({'detail': f'Ошибка отправки письма: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def verify_email(request):
    token = request.query_params.get('token')
    if not token:
        return Response({'detail': 'Токен обязателен.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        verification = EmailVerification.objects.get(token=token, is_used=False)
    except EmailVerification.DoesNotExist:
        return Response({'detail': 'Неверный или использованный токен.'}, status=status.HTTP_400_BAD_REQUEST)

    from django.utils import timezone
    from datetime import timedelta
    if timezone.now() - verification.created_at > timedelta(hours=24):
        return Response({'detail': 'Ссылка истекла. Запросите новую.'}, status=status.HTTP_400_BAD_REQUEST)

    verification.is_used = True
    verification.save()

    verification.user.is_email_verified = True
    verification.user.save()

    return Response({'detail': 'Email успешно верифицирован!'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_email_verification(request):
    return Response({
        'is_verified': request.user.is_email_verified,
        'email': request.user.email,
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_request(request):
    email = request.data.get('email')
    if not email:
        return Response({'detail': 'Email обязателен.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'detail': 'Если пользователь с таким email существует, письмо будет отправлено.'})

    from .models import PasswordResetToken
    reset_token = PasswordResetToken.objects.create(user=user)

    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    reset_link = f"{frontend_url}/auth/reset-password?token={reset_token.token}"

    try:
        send_mail(
            subject='Сброс пароля - CareerHub',
            message=f'Для сброса пароля перейдите по ссылке: {reset_link}',
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@careerhub.com'),
            recipient_list=[email],
            fail_silently=False,
        )
        return Response({'detail': 'Если пользователь с таким email существует, письмо для сброса пароля отправлено.'})
    except Exception as e:
        return Response({'detail': f'Ошибка отправки письма: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_confirm(request):
    token = request.data.get('token')
    new_password = request.data.get('new_password')

    if not token or not new_password:
        return Response({'detail': 'Токен и новый пароль обязательны.'}, status=status.HTTP_400_BAD_REQUEST)

    from .models import PasswordResetToken
    try:
        reset_token = PasswordResetToken.objects.get(token=token, is_used=False)
    except PasswordResetToken.DoesNotExist:
        return Response({'detail': 'Неверный или использованный токен.'}, status=status.HTTP_400_BAD_REQUEST)

    from datetime import timedelta
    if timezone.now() - reset_token.created_at > timedelta(hours=24):
        return Response({'detail': 'Ссылка истекла. Запросите новую.'}, status=status.HTTP_400_BAD_REQUEST)

    user = reset_token.user
    user.set_password(new_password)
    user.save()

    reset_token.is_used = True
    reset_token.save()

    return Response({'detail': 'Пароль успешно изменён.'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def conversations_list(request):
    user = request.user
    sent = DirectMessage.objects.filter(sender=user).values('recipient').annotate(
        last_id=Max('id')
    )
    received = DirectMessage.objects.filter(recipient=user).values('sender').annotate(
        last_id=Max('id')
    )

    user_last_msg = {}
    for item in sent:
        uid = item['recipient']
        if uid not in user_last_msg or item['last_id'] > user_last_msg[uid]['last_id']:
            user_last_msg[uid] = {'last_id': item['last_id'], 'direction': 'sent'}
    for item in received:
        uid = item['sender']
        if uid not in user_last_msg or item['last_id'] > user_last_msg[uid]['last_id']:
            user_last_msg[uid] = {'last_id': item['last_id'], 'direction': 'received'}

    conversations = []
    for uid, info in user_last_msg.items():
        other_user = User.objects.get(id=uid)
        last_msg = DirectMessage.objects.get(id=info['last_id'])
        unread = DirectMessage.objects.filter(sender=other_user, recipient=user, is_read=False).count()
        conversations.append({
            'user': UserSerializer(other_user).data,
            'last_message': DirectMessageSerializer(last_msg).data,
            'unread_count': unread,
        })

    conversations.sort(key=lambda c: c['last_message']['created_at'], reverse=True)
    return Response(conversations)


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def direct_messages(request, user_id):
    try:
        other_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'detail': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        messages = DirectMessage.objects.filter(
            Q(sender=request.user, recipient=other_user) |
            Q(sender=other_user, recipient=request.user)
        )
        messages.filter(sender=other_user, recipient=request.user, is_read=False).update(is_read=True)
        serializer = DirectMessageSerializer(messages, many=True)
        return Response(serializer.data)

    content = request.data.get('content', '').strip()
    if not content:
        return Response({'detail': 'Сообщение обязательно.'}, status=status.HTTP_400_BAD_REQUEST)

    msg = DirectMessage.objects.create(
        sender=request.user,
        recipient=other_user,
        content=content,
    )

    sender_id = request.user.id

    Notification.objects.create(
        user=other_user,
        notification_type='message',
        title=f'Новое сообщение от {request.user.username}',
        message=content[:200],
        link=f'/chat?user={sender_id}',
    )

    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{other_user.id}',
            {
                'type': 'send_notification',
                'notification_type': 'message',
                'title': f'Новое сообщение от {request.user.username}',
                'message': content[:200],
                'data': {'link': f'/chat?user={sender_id}'},
            }
        )
        room_name = f'{min(sender_id, other_user.id)}_{max(sender_id, other_user.id)}'
        async_to_sync(channel_layer.group_send)(
            f'chat_{room_name}',
            {
                'type': 'chat_message',
                'message': content,
                'sender_id': sender_id,
                'sender_name': request.user.username,
            }
        )
    except Exception:
        pass

    return Response(DirectMessageSerializer(msg).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def employer_chat_users(request):
    if request.user.role != 'student':
        return Response({'detail': 'Только для студентов.'}, status=status.HTTP_403_FORBIDDEN)

    employer_ids = Application.objects.filter(
        resume__student=request.user.student_profile
    ).values_list('job__employer__user_id', flat=True).distinct()

    employers = User.objects.filter(id__in=employer_ids, role='employer')
    serializer = UserSerializer(employers, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsEmployer])
def parse_somon_tj(request):
    from .parsing_service import parse_somon_tj_jobs
    
    max_jobs = request.data.get('max_jobs', 20)
    try:
        max_jobs = int(max_jobs)
    except (ValueError, TypeError):
        max_jobs = 20
    
    max_jobs = min(max(max_jobs, 1), 50)
    
    result = parse_somon_tj_jobs(max_jobs)
    return Response(result)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def generate_job_pdf(request, job_id):
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return Response({'detail': 'Вакансия не найдена.'}, status=status.HTTP_404_NOT_FOUND)

    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor, white, black, Color
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.graphics.shapes import Drawing, Rect, Line, Circle
    from reportlab.graphics import renderPDF
    import os

    pdfmetrics.registerFont(TTFont('Arial', os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', 'arial.ttf')))
    pdfmetrics.registerFont(TTFont('Arial-Bold', os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', 'arialbd.ttf')))

    style = request.query_params.get('style', 'classic')
    buffer = BytesIO()

    if style == 'classic':
        _build_classic(buffer, job)
    elif style == 'modern':
        _build_modern(buffer, job)
    elif style == 'minimal':
        _build_minimal(buffer, job)
    elif style == 'creative':
        _build_creative(buffer, job)
    else:
        _build_classic(buffer, job)

    buffer.seek(0)
    style_names = {'classic': 'Классический', 'modern': 'Современный', 'minimal': 'Минималистичный', 'creative': 'Креативный'}
    filename = f'vacancy_{job.id}_{style_names.get(style, style)}.pdf'
    return FileResponse(buffer, as_attachment=True, filename=filename)


def _build_classic(buffer, job):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor, white
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from django.utils import timezone
    import os

    ACCENT = HexColor('#059669')
    ACCENT_LIGHT = HexColor('#D1FAE5')
    BG = HexColor('#F0FDF4')
    TEXT = HexColor('#14532D')
    MUTED = HexColor('#4D7C0F')
    BORDER = HexColor('#BBF7D0')

    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=22*mm, leftMargin=22*mm, topMargin=20*mm, bottomMargin=20*mm)

    ts = ParagraphStyle('ts', fontName='Arial-Bold', fontSize=24, textColor=ACCENT, leading=28, spaceAfter=2)
    cs = ParagraphStyle('cs', fontName='Arial', fontSize=12, textColor=TEXT, leading=15, spaceAfter=1)
    hs = ParagraphStyle('hs', fontName='Arial-Bold', fontSize=12, textColor=ACCENT, leading=15, spaceBefore=14, spaceAfter=6)
    bs = ParagraphStyle('bs', fontName='Arial', fontSize=10, textColor=TEXT, leading=14, spaceAfter=3)
    fs = ParagraphStyle('fs', fontName='Arial', fontSize=7.5, textColor=MUTED, leading=10)

    story = []
    story.append(Paragraph(job.title, ts))
    story.append(HRFlowable(width='100%', thickness=3, color=ACCENT, spaceAfter=8, spaceBefore=4))
    story.append(Paragraph(f'{job.employer.company_name}', cs))
    if job.employer.address:
        story.append(Paragraph(job.employer.address, cs))
    story.append(Spacer(1, 10))

    salary = format_salary_pdf(job.salary_min, job.salary_max)
    schedule = format_schedule_pdf(job.schedule)
    work_fmt = format_work_format_pdf(job.work_format)
    exp = 'Не требуется' if not job.experience_required else 'Требуется'
    cat = job.category.name if job.category else '—'
    dt = job.created_at.strftime('%d.%m.%Y')

    rows = [
        [Paragraph('<b>Параметр</b>', ParagraphStyle('h', fontName='Arial-Bold', fontSize=9, textColor=white, leading=12)),
         Paragraph('<b>Значение</b>', ParagraphStyle('h', fontName='Arial-Bold', fontSize=9, textColor=white, leading=12))],
        [Paragraph('Зарплата', ParagraphStyle('c', fontName='Arial', fontSize=9.5, textColor=TEXT, leading=12)),
         Paragraph(f'<b>{salary}</b>', ParagraphStyle('cb', fontName='Arial-Bold', fontSize=9.5, textColor=ACCENT, leading=12))],
        [Paragraph('График', ParagraphStyle('c', fontName='Arial', fontSize=9.5, textColor=TEXT, leading=12)),
         Paragraph(schedule, ParagraphStyle('c', fontName='Arial', fontSize=9.5, textColor=TEXT, leading=12))],
        [Paragraph('Формат', ParagraphStyle('c', fontName='Arial', fontSize=9.5, textColor=TEXT, leading=12)),
         Paragraph(work_fmt, ParagraphStyle('c', fontName='Arial', fontSize=9.5, textColor=TEXT, leading=12))],
        [Paragraph('Возраст', ParagraphStyle('c', fontName='Arial', fontSize=9.5, textColor=TEXT, leading=12)),
         Paragraph(f'от {job.min_age} лет', ParagraphStyle('c', fontName='Arial', fontSize=9.5, textColor=TEXT, leading=12))],
        [Paragraph('Опыт', ParagraphStyle('c', fontName='Arial', fontSize=9.5, textColor=TEXT, leading=12)),
         Paragraph(exp, ParagraphStyle('c', fontName='Arial', fontSize=9.5, textColor=TEXT, leading=12))],
        [Paragraph('Категория', ParagraphStyle('c', fontName='Arial', fontSize=9.5, textColor=TEXT, leading=12)),
         Paragraph(cat, ParagraphStyle('c', fontName='Arial', fontSize=9.5, textColor=TEXT, leading=12))],
        [Paragraph('Дата', ParagraphStyle('c', fontName='Arial', fontSize=9.5, textColor=TEXT, leading=12)),
         Paragraph(dt, ParagraphStyle('c', fontName='Arial', fontSize=9.5, textColor=TEXT, leading=12))],
    ]

    t = Table(rows, colWidths=[55*mm, 115*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
        ('TEXTCOLOR', (0, 0), (-1, 0), white), 
        ('BACKGROUND', (0, 1), (-1, -1), BG),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BG, white]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, ACCENT),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    story.append(Paragraph('Описание вакансии', hs))
    story.append(HRFlowable(width='100%', thickness=1, color=ACCENT_LIGHT, spaceAfter=6))
    for line in job.description.split('\n'):
        if line.strip():
            story.append(Paragraph(line.strip(), bs))
    story.append(Spacer(1, 10))

    story.append(Paragraph('О компании', hs))
    story.append(HRFlowable(width='100%', thickness=1, color=ACCENT_LIGHT, spaceAfter=6))
    desc = job.employer.description or '—'
    for line in desc.split('\n'):
        if line.strip():
            story.append(Paragraph(line.strip(), bs))
    if job.employer.website:
        story.append(Spacer(1, 4))
        story.append(Paragraph(f'Сайт: {job.employer.website}', bs))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width='100%', thickness=1, color=ACCENT_LIGHT, spaceAfter=6))
    story.append(Paragraph(f'CareerHub  •  {timezone.now().strftime("%d.%m.%Y")}', fs))
    doc.build(story)


def _build_modern(buffer, job):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor, white
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Flowable
    from django.utils import timezone
    import os

    ACCENT = HexColor('#2563EB')
    DARK = HexColor('#1E3A5F')
    LIGHT_BG = HexColor('#F0F7FF')
    TEXT = HexColor('#1E293B')
    MUTED = HexColor('#64748B')
    BORDER = HexColor('#CBD5E1')
    TAG_BG = HexColor('#DBEAFE')

    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=0, bottomMargin=15*mm)

    header_style = ParagraphStyle('hdr', fontName='Arial-Bold', fontSize=11, textColor=white, leading=14)

    d = Drawing(170*mm, 32*mm)
    d.add(Rect(0, 0, 170*mm, 32*mm, fillColor=DARK, strokeColor=None))
    d.add(Rect(0, 0, 170*mm, 3*mm, fillColor=ACCENT, strokeColor=None))
    story = []
    story.append(Spacer(1, 2*mm))

    from reportlab.platypus import Flowable
    class HeaderBlock(Flowable):
        def __init__(self, title, company, address, w=170*mm, h=30*mm):
            Flowable.__init__(self)
            self.title = title
            self.company = company
            self.address = address
            self.w = w
            self.h = h
        def wrap(self, aW, aH):
            return self.w, self.h
        def draw(self):
            self.canv.setFillColor(DARK)
            self.canv.roundRect(0, 0, self.w, self.h, 4, fill=1, stroke=0)
            self.canv.setFillColor(ACCENT)
            self.canv.rect(0, 0, self.w, 2.5, fill=1, stroke=0)
            self.canv.setFillColor(white)
            self.canv.setFont('Arial-Bold', 20)
            self.canv.drawString(12, self.h - 22, self.title)
            self.canv.setFont('Arial', 9.5)
            self.canv.drawString(12, self.h - 36, self.company)
            if self.address:
                self.canv.setFillColor(HexColor('#93C5FD'))
                self.canv.setFont('Arial', 8.5)
                self.canv.drawString(12, self.h - 48, self.address)

    story.append(HeaderBlock(job.title, job.employer.company_name, job.employer.address or ''))
    story.append(Spacer(1, 10))

    salary = format_salary_pdf(job.salary_min, job.salary_max)
    schedule = format_schedule_pdf(job.schedule)
    work_fmt = format_work_format_pdf(job.work_format)
    exp = 'Нет' if not job.experience_required else 'Да'
    cat = job.category.name if job.category else '—'

    tags = [
        salary,
        schedule,
        work_fmt,
        f'от {job.min_age}',
        exp if exp == 'Нет' else 'Требуется',
    ]

    tag_ts = ParagraphStyle('tag', fontName='Arial', fontSize=8, textColor=DARK, leading=10)

    tag_data = [[Paragraph(f'<b>{text}</b>', tag_ts) for text in tags]]
    tag_t = Table(tag_data, colWidths=[34*mm]*5)
    tag_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    story.append(tag_t)
    story.append(Spacer(1, 12))

    hs = ParagraphStyle('hs', fontName='Arial-Bold', fontSize=13, textColor=DARK, leading=16, spaceBefore=4, spaceAfter=6)
    bs = ParagraphStyle('bs', fontName='Arial', fontSize=10, textColor=TEXT, leading=14, spaceAfter=3)
    fs = ParagraphStyle('fs', fontName='Arial', fontSize=7.5, textColor=MUTED, leading=10)

    class SectionTitle(Flowable):
        def __init__(self, text, w=170*mm):
            Flowable.__init__(self)
            self.text = text
            self.w = w
        def wrap(self, aW, aH):
            return self.w, 10*mm
        def draw(self):
            self.canv.setFillColor(ACCENT)
            self.canv.roundRect(0, 2*mm, 4, 7*mm, 2, fill=1, stroke=0)
            self.canv.setFillColor(DARK)
            self.canv.setFont('Arial-Bold', 12)
            self.canv.drawString(10, 3.5*mm, self.text)

    story.append(SectionTitle('Описание вакансии'))
    story.append(Spacer(1, 2*mm))
    for line in job.description.split('\n'):
        if line.strip():
            story.append(Paragraph(line.strip(), bs))
    story.append(Spacer(1, 10))

    story.append(SectionTitle('О компании'))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(f'<b>{job.employer.company_name}</b>', ParagraphStyle('cn', fontName='Arial-Bold', fontSize=11, textColor=DARK, leading=14, spaceAfter=4)))
    desc = job.employer.description or '—'
    for line in desc.split('\n'):
        if line.strip():
            story.append(Paragraph(line.strip(), bs))
    if job.employer.website:
        story.append(Spacer(1, 4))
        story.append(Paragraph(f'<font color="#2563EB">{job.employer.website}</font>', bs))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER, spaceAfter=6))
    story.append(Paragraph(f'CareerHub  •  {job.created_at.strftime("%d.%m.%Y")}  •  {timezone.now().strftime("%H:%M")}', fs))

    doc.build(story)


def _build_minimal(buffer, job):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor, white
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from django.utils import timezone
    import os

    TEXT = HexColor('#18181B')
    MUTED = HexColor('#71717A')
    LIGHT = HexColor('#FAFAFA')
    LINE = HexColor('#E4E4E7')
    ACCENT = HexColor('#27272A')

    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=25*mm, leftMargin=25*mm, topMargin=25*mm, bottomMargin=20*mm)

    ts = ParagraphStyle('ts', fontName='Arial-Bold', fontSize=26, textColor=TEXT, leading=30, spaceAfter=4)
    cs = ParagraphStyle('cs', fontName='Arial', fontSize=10, textColor=MUTED, leading=13, spaceAfter=1)
    bs = ParagraphStyle('bs', fontName='Arial', fontSize=10, textColor=TEXT, leading=14, spaceAfter=3)
    fs = ParagraphStyle('fs', fontName='Arial', fontSize=7.5, textColor=MUTED, leading=10)

    story = []
    story.append(Paragraph(job.title, ts))
    story.append(Spacer(1, 2*mm))
    story.append(HRFlowable(width='30%', thickness=2, color=TEXT, spaceAfter=8, hAlign='LEFT'))
    story.append(Paragraph(job.employer.company_name, ParagraphStyle('co', fontName='Arial', fontSize=11, textColor=TEXT, leading=14)))
    if job.employer.address:
        story.append(Paragraph(job.employer.address, cs))
    story.append(Spacer(1, 14))

    salary = format_salary_pdf(job.salary_min, job.salary_max)
    schedule = format_schedule_pdf(job.schedule)
    work_fmt = format_work_format_pdf(job.work_format)
    exp = 'Не требуется' if not job.experience_required else 'Требуется'
    cat = job.category.name if job.category else '—'

    label_s = ParagraphStyle('lb', fontName='Arial', fontSize=8, textColor=MUTED, leading=10, spaceBefore=4)
    value_s = ParagraphStyle('vl', fontName='Arial-Bold', fontSize=10, textColor=TEXT, leading=13)

    kv_data = [
        [Paragraph('ЗАРПЛАТА', label_s), Paragraph('ГРАФИК', label_s), Paragraph('ФОРМАТ', label_s)],
        [Paragraph(f'<b>{salary}</b>', value_s), Paragraph(schedule, value_s), Paragraph(work_fmt, value_s)],
        [Paragraph('ВОЗРАСТ', label_s), Paragraph('ОПЫТ', label_s), Paragraph('КАТЕГОРИЯ', label_s)],
        [Paragraph(f'от {job.min_age} лет', value_s), Paragraph(exp, value_s), Paragraph(cat, value_s)],
    ]

    kv_t = Table(kv_data, colWidths=[56*mm, 56*mm, 56*mm])
    kv_t.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('LINEBELOW', (0, 1), (-1, 1), 0.5, LINE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(kv_t)
    story.append(Spacer(1, 16))

    story.append(HRFlowable(width='100%', thickness=0.5, color=LINE, spaceAfter=10))

    story.append(Paragraph('ОПИСАНИЕ', ParagraphStyle('sh', fontName='Arial-Bold', fontSize=9, textColor=MUTED, leading=12, spaceAfter=8)))
    for line in job.description.split('\n'):
        if line.strip():
            story.append(Paragraph(line.strip(), bs))
    story.append(Spacer(1, 14))

    story.append(HRFlowable(width='100%', thickness=0.5, color=LINE, spaceAfter=10))
    story.append(Paragraph('КОМПАНИЯ', ParagraphStyle('sh2', fontName='Arial-Bold', fontSize=9, textColor=MUTED, leading=12, spaceAfter=8)))
    story.append(Paragraph(job.employer.company_name, ParagraphStyle('cn', fontName='Arial-Bold', fontSize=11, textColor=TEXT, leading=14, spaceAfter=4)))
    desc = job.employer.description or '—'
    for line in desc.split('\n'):
        if line.strip():
            story.append(Paragraph(line.strip(), bs))

    story.append(Spacer(1, 24))
    story.append(HRFlowable(width='100%', thickness=0.5, color=LINE, spaceAfter=6))
    story.append(Paragraph(f'CareerHub  •  {job.created_at.strftime("%d.%m.%Y")}', fs))

    doc.build(story)


def _build_creative(buffer, job):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor, white
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Flowable
    from django.utils import timezone
    import os

    ORANGE = HexColor('#EA580C')
    ORANGE_DARK = HexColor('#C2410C')
    ORANGE_LIGHT = HexColor('#FFF7ED')
    AMBER = HexColor('#F59E0B')
    TEXT = HexColor('#292524')
    MUTED = HexColor('#78716C')
    BORDER = HexColor('#FED7AA')
    BG_STRIPE = HexColor('#FFFBEB')

    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=0, bottomMargin=15*mm)

    class CreativeHeader(Flowable):
        def __init__(self, title, company, address, w=170*mm, h=36*mm):
            Flowable.__init__(self)
            self.title = title
            self.company = company
            self.address = address
            self.w = w
            self.h = h
        def wrap(self, aW, aH):
            return self.w, self.h
        def draw(self):
            c = self.canv
            c.setFillColor(ORANGE)
            c.roundRect(0, 0, self.w, self.h, 6, fill=1, stroke=0)
            c.setFillColor(white)
            c.setFont('Arial-Bold', 22)
            c.drawString(16, self.h - 24, self.title)
            c.setFont('Arial', 10)
            c.drawString(16, self.h - 38, self.company)
            if self.address:
                c.setFont('Arial', 8.5)
                c.setFillColor(HexColor('#FED7AA'))
                c.drawString(16, self.h - 50, self.address)
            c.setFillColor(AMBER)
            c.circle(self.w - 18, self.h - 18, 14, fill=1, stroke=0)
            c.setFillColor(white)
            c.setFont('Arial-Bold', 11)
            c.drawCentredString(self.w - 18, self.h - 22, '★')

    story = []
    story.append(Spacer(1, 3*mm))
    story.append(CreativeHeader(job.title, job.employer.company_name, job.employer.address or ''))
    story.append(Spacer(1, 10))

    salary = format_salary_pdf(job.salary_min, job.salary_max)
    schedule = format_schedule_pdf(job.schedule)
    work_fmt = format_work_format_pdf(job.work_format)
    exp = 'Не требуется' if not job.experience_required else 'Требуется'
    cat = job.category.name if job.category else '—'

    icon_ts = ParagraphStyle('ic', fontName='Arial-Bold', fontSize=12, textColor=ORANGE, leading=15, alignment=1)
    val_ts = ParagraphStyle('vl', fontName='Arial-Bold', fontSize=10, textColor=TEXT, leading=13, alignment=1)
    lbl_ts = ParagraphStyle('lb', fontName='Arial', fontSize=7.5, textColor=MUTED, leading=10, alignment=1)

    cards = [
        (salary, 'Зарплата'),
        (schedule, 'График'),
        (work_fmt, 'Формат'),
        (f'от {job.min_age}', 'Возраст'),
    ]

    card_data = [[
        Paragraph(f'<b>{val}</b>', val_ts) for val, _ in cards
    ], [
        Paragraph(lbl, lbl_ts) for _, lbl in cards
    ]]

    card_t = Table(card_data, colWidths=[42.5*mm]*4)
    card_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ORANGE_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 2),
        ('TOPPADDING', (0, 1), (-1, 1), 2),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(card_t)
    story.append(Spacer(1, 6))

    info_rows = [
        [Paragraph('Опыт', ParagraphStyle('il', fontName='Arial', fontSize=9, textColor=MUTED, leading=12)),
         Paragraph(exp, ParagraphStyle('iv', fontName='Arial-Bold', fontSize=9, textColor=TEXT, leading=12))],
        [Paragraph('Категория', ParagraphStyle('il', fontName='Arial', fontSize=9, textColor=MUTED, leading=12)),
         Paragraph(cat, ParagraphStyle('iv', fontName='Arial-Bold', fontSize=9, textColor=TEXT, leading=12))],
        [Paragraph('Опубликовано', ParagraphStyle('il', fontName='Arial', fontSize=9, textColor=MUTED, leading=12)),
         Paragraph(job.created_at.strftime('%d.%m.%Y'), ParagraphStyle('iv', fontName='Arial-Bold', fontSize=9, textColor=TEXT, leading=12))],
    ]
    info_t = Table(info_rows, colWidths=[55*mm, 115*mm])
    info_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_STRIPE),
        ('LINEBELOW', (0, 0), (-1, -1), 0.3, BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(info_t)
    story.append(Spacer(1, 14))

    bs = ParagraphStyle('bs', fontName='Arial', fontSize=10, textColor=TEXT, leading=14, spaceAfter=3)
    fs = ParagraphStyle('fs', fontName='Arial', fontSize=7.5, textColor=MUTED, leading=10)

    class CreativeSection(Flowable):
        def __init__(self, text, w=170*mm):
            Flowable.__init__(self)
            self.text = text
            self.w = w
        def wrap(self, aW, aH):
            return self.w, 9*mm
        def draw(self):
            self.canv.setFillColor(ORANGE)
            self.canv.roundRect(0, 0, self.w, 7*mm, 3, fill=1, stroke=0)
            self.canv.setFillColor(white)
            self.canv.setFont('Arial-Bold', 11)
            self.canv.drawString(10, 1.8*mm, self.text)

    story.append(CreativeSection('Описание вакансии'))
    story.append(Spacer(1, 4*mm))
    for line in job.description.split('\n'):
        if line.strip():
            story.append(Paragraph(line.strip(), bs))
    story.append(Spacer(1, 12))

    story.append(CreativeSection('О компании'))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(job.employer.company_name, ParagraphStyle('cn', fontName='Arial-Bold', fontSize=11, textColor=ORANGE_DARK, leading=14, spaceAfter=4)))
    desc = job.employer.description or '—'
    for line in desc.split('\n'):
        if line.strip():
            story.append(Paragraph(line.strip(), bs))
    if job.employer.website:
        story.append(Spacer(1, 4))
        story.append(Paragraph(f'<font color="#EA580C">{job.employer.website}</font>', bs))

    story.append(Spacer(1, 18))
    story.append(HRFlowable(width='100%', thickness=1, color=BORDER, spaceAfter=6))
    story.append(Paragraph(f'CareerHub  ★  {job.created_at.strftime("%d.%m.%Y")}', fs))

    doc.build(story)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def generate_resume_pdf(request, resume_id):
    try:
        resume = Resume.objects.get(id=resume_id)
    except Resume.DoesNotExist:
        return Response({'detail': 'Резюме не найдено.'}, status=status.HTTP_404_NOT_FOUND)

    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor, white, black
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os

    pdfmetrics.registerFont(TTFont('Arial', os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', 'arial.ttf')))
    pdfmetrics.registerFont(TTFont('Arial-Bold', os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', 'arialbd.ttf')))

    style = resume.style or 'modern'

    STYLES = {
        'classic': {
            'accent': HexColor('#10B981'),
            'bg_table': HexColor('#F0FDF4'),
            'border': HexColor('#D1D5DB'),
            'text_dark': HexColor('#1F2937'),
            'text_muted': HexColor('#6B7280'),
            'hr_thick': 2,
            'title_size': 20,
            'layout': 'traditional',
        },
        'modern': {
            'accent': HexColor('#3B82F6'),
            'bg_table': HexColor('#F0F4FF'),
            'border': HexColor('#D1D5DB'),
            'text_dark': HexColor('#1E293B'),
            'text_muted': HexColor('#64748B'),
            'hr_thick': 2,
            'title_size': 22,
            'layout': 'clean',
        },
        'minimal': {
            'accent': HexColor('#374151'),
            'bg_table': HexColor('#F9FAFB'),
            'border': HexColor('#E5E7EB'),
            'text_dark': HexColor('#111827'),
            'text_muted': HexColor('#6B7280'),
            'hr_thick': 1,
            'title_size': 20,
            'layout': 'minimal',
        },
        'creative': {
            'accent': HexColor('#D97706'),
            'bg_table': HexColor('#FFFBEB'),
            'border': HexColor('#FDE68A'),
            'text_dark': HexColor('#1C1917'),
            'text_muted': HexColor('#78716C'),
            'hr_thick': 3,
            'title_size': 24,
            'layout': 'creative',
        },
    }

    s = STYLES.get(style, STYLES['modern'])
    ACCENT = s['accent']
    BG_TABLE = s['bg_table']
    BORDER = s['border']
    TEXT_DARK = s['text_dark']
    TEXT_MUTED = s['text_muted']

    profile = resume.student
    user = profile.user

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)

    title_style = ParagraphStyle('Title', fontName='Arial-Bold', fontSize=s['title_size'], spaceAfter=4, textColor=ACCENT, leading=s['title_size'] + 4)
    name_style = ParagraphStyle('Name', fontName='Arial-Bold', fontSize=14, spaceAfter=2, textColor=TEXT_DARK, leading=18)
    subtitle_style = ParagraphStyle('Subtitle', fontName='Arial', fontSize=11, spaceAfter=2, textColor=TEXT_MUTED, leading=14)
    heading_style = ParagraphStyle('Heading', fontName='Arial-Bold', fontSize=13, spaceAfter=8, spaceBefore=16, textColor=TEXT_DARK, leading=16)
    body_style = ParagraphStyle('Body', fontName='Arial', fontSize=10.5, spaceAfter=5, textColor=TEXT_DARK, leading=15)
    small_style = ParagraphStyle('Small', fontName='Arial', fontSize=8.5, textColor=TEXT_MUTED, leading=11)
    cell_style = ParagraphStyle('Cell', fontName='Arial', fontSize=10, textColor=TEXT_DARK, leading=13)
    cell_bold = ParagraphStyle('CellBold', fontName='Arial-Bold', fontSize=10, textColor=TEXT_DARK, leading=13)
    skill_style = ParagraphStyle('Skill', fontName='Arial', fontSize=10, textColor=TEXT_DARK, leading=13)

    story = []

    if style == 'creative':
        story.append(Spacer(1, 6))

    story.append(Paragraph(resume.title, title_style))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width='100%', thickness=s['hr_thick'], color=ACCENT, spaceAfter=10))

    story.append(Paragraph(user.username, name_style))
    if user.email:
        story.append(Paragraph(user.email, subtitle_style))
    story.append(Spacer(1, 8))

    info_rows = []
    if profile.university:
        info_rows.append([Paragraph('Университет', cell_style), Paragraph(profile.university, cell_style)])
    if profile.faculty:
        info_rows.append([Paragraph('Факультет', cell_style), Paragraph(profile.faculty, cell_style)])
    if profile.course:
        info_rows.append([Paragraph('Курс', cell_style), Paragraph(f'{profile.course} курс', cell_style)])
    if profile.city:
        info_rows.append([Paragraph('Город', cell_style), Paragraph(profile.city, cell_style)])
    info_rows.append([Paragraph('График', cell_style), Paragraph(format_schedule_pdf(resume.schedule_type), cell_style)])
    info_rows.append([Paragraph('Формат', cell_style), Paragraph(format_work_format_pdf(resume.work_format), cell_style)])
    if resume.github_url:
        info_rows.append([Paragraph('GitHub', cell_style), Paragraph(resume.github_url, cell_style)])
    if resume.portfolio_url:
        info_rows.append([Paragraph('Портфолио', cell_style), Paragraph(resume.portfolio_url, cell_style)])
    if resume.linkedin_url:
        info_rows.append([Paragraph('LinkedIn', cell_style), Paragraph(resume.linkedin_url, cell_style)])

    if info_rows:
        header_row = [Paragraph('<b>Параметр</b>', cell_bold), Paragraph('<b>Значение</b>', cell_bold)]
        all_rows = [header_row] + info_rows
        table = Table(all_rows, colWidths=[55*mm, 115*mm])

        table_styles = [
            ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('BACKGROUND', (0, 1), (-1, -1), BG_TABLE),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BG_TABLE, white]),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]

        if style == 'minimal':
            table_styles.append(('LINEBELOW', (0, 0), (-1, 0), 1, ACCENT))
            table_styles = [t for t in table_styles if t[0] != 'GRID']

        table.setStyle(TableStyle(table_styles))
        story.append(table)
        story.append(Spacer(1, 16))

    if resume.about:
        story.append(Paragraph('О себе', heading_style))
        story.append(HRFlowable(width='100%', thickness=1, color=BORDER, spaceAfter=8))
        for line in resume.about.split('\n'):
            line = line.strip()
            if line:
                story.append(Paragraph(line, body_style))
        story.append(Spacer(1, 8))

    if resume.skills:
        story.append(Paragraph('Навыки', heading_style))
        story.append(HRFlowable(width='100%', thickness=1, color=BORDER, spaceAfter=8))

        skill_rows = []
        for i in range(0, len(resume.skills), 3):
            row_skills = resume.skills[i:i+3]
            row = [Paragraph(f'\u2022  {s}', skill_style) for s in row_skills]
            while len(row) < 3:
                row.append(Paragraph('', cell_style))
            skill_rows.append(row)

        if skill_rows:
            skill_table = Table(skill_rows, colWidths=[56*mm, 56*mm, 58*mm])
            skill_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(skill_table)

    story.append(Spacer(1, 24))
    story.append(HRFlowable(width='100%', thickness=1, color=BORDER, spaceAfter=8))
    story.append(Paragraph(f'Сгенерировано на CareerHub  \u2022  {timezone.now().strftime("%d.%m.%Y %H:%M")}', small_style))

    doc.build(story)
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename=f'resume_{resume.id}_{style}.pdf')


def format_salary_pdf(min_sal, max_sal):
    if min_sal and max_sal:
        if min_sal == max_sal:
            return f"{min_sal:,} сомони".replace(',', ' ')
        return f"{min_sal:,} - {max_sal:,} сомони".replace(',', ' ')
    elif min_sal:
        return f"от {min_sal:,} сомони".replace(',', ' ')
    elif max_sal:
        return f"до {max_sal:,} сомони".replace(',', ' ')
    return 'По договорённости'


def format_schedule_pdf(schedule):
    mapping = {'flexible': 'Гибкий', 'part_time': '2-4 часа', 'full_time': 'Полная занятость'}
    return mapping.get(schedule, schedule)


def format_work_format_pdf(fmt):
    mapping = {'online': 'Онлайн', 'offline': 'Офлайн', 'hybrid': 'Гибрид'}
    return mapping.get(fmt, fmt)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'detail': 'Все уведомления отмечены как прочитанные.'})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'detail': 'Уведомление отмечено как прочитанное.'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def calculate_route(request):
    user_location = request.data.get('user_location', '').strip()
    job_lat = request.data.get('job_lat')
    job_lng = request.data.get('job_lng')

    if not user_location or not job_lat or not job_lng:
        return Response({'detail': 'Укажите место проживания и координаты работы.'}, status=status.HTTP_400_BAD_REQUEST)

    import urllib.request
    import urllib.parse
    import json

    try:
        geocode_url = f'https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(user_location)}&format=json&limit=5&countrycodes=tj,ru'
        req = urllib.request.Request(geocode_url, headers={'User-Agent': 'CareerHub/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            geocode_data = json.loads(resp.read().decode())

        if not geocode_data:
            geocode_url2 = f'https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(user_location)}&format=json&limit=3'
            req2 = urllib.request.Request(geocode_url2, headers={'User-Agent': 'CareerHub/1.0'})
            with urllib.request.urlopen(req2, timeout=10) as resp2:
                geocode_data = json.loads(resp2.read().decode())

        if not geocode_data:
            return Response({'detail': 'Не удалось найти координаты вашего места проживания.'}, status=status.HTTP_400_BAD_REQUEST)

        best = geocode_data[0]
        for item in geocode_data:
            display = item.get('display_name', '').lower()
            if 'tajikistan' in display or 'таджикистан' in display or 'dushanbe' in display or 'душанбе' in display:
                best = item
                break

        user_lat = float(best['lat'])
        user_lng = float(best['lon'])
        display_name = best.get('display_name', user_location)

        osrm_url = f'https://router.project-osrm.org/route/v1/driving/{user_lng},{user_lat};{job_lng},{job_lat}?overview=full&steps=true&geometries=geojson'
        req2 = urllib.request.Request(osrm_url, headers={'User-Agent': 'CareerHub/1.0'})
        with urllib.request.urlopen(req2, timeout=15) as resp2:
            route_data = json.loads(resp2.read().decode())

        if route_data.get('code') != 'Ok' or not route_data.get('routes'):
            return Response({'detail': 'Не удалось построить маршрут.'}, status=status.HTTP_400_BAD_REQUEST)

        route = route_data['routes'][0]
        distance_km = round(route['distance'] / 1000, 1)
        duration_min = round(route['duration'] / 60)

        hours = duration_min // 60
        minutes = duration_min % 60
        if hours > 0:
            duration_text = f'{hours} ч {minutes} мин'
        else:
            duration_text = f'{minutes} мин'

        steps = []
        for leg in route['legs']:
            for step in leg['steps']:
                maneuver = step.get('maneuver', {})
                instruction = step.get('name', '')
                modifier = maneuver.get('modifier', '')
                maneuver_type = maneuver.get('type', '')

                if maneuver_type == 'depart':
                    text = f'Начните движение'
                elif maneuver_type == 'arrive':
                    text = f'Прибытие'
                elif maneuver_type == 'turn':
                    direction = {'left': 'налево', 'right': 'направо', 'slight left': 'легкое поворот налево', 'slight right': 'легкое поворот направо', 'uturn': 'разворот'}.get(modifier, 'поворот')
                    text = f'Поверните {direction}'
                    if instruction:
                        text += f' на {instruction}'
                elif maneuver_type == 'new name':
                    text = f'Продолжайте по {instruction}' if instruction else 'Продолжайте движение'
                elif maneuver_type == 'merge':
                    text = f'Встаньте на полосу'
                elif maneuver_type == 'roundabout':
                    text = f'На круговом движении'
                else:
                    text = maneuver_type.replace('_', ' ').capitalize()
                    if instruction:
                        text += f' ({instruction})'

                steps.append({
                    'text': text,
                    'distance': round(step.get('distance', 0)),
                })

        return Response({
            'distance_km': distance_km,
            'distance_text': f'{distance_km} км',
            'duration_text': duration_text,
            'duration_minutes': duration_min,
            'user_coordinates': {'lat': user_lat, 'lng': user_lng},
            'user_address': display_name,
            'polyline': route['geometry']['coordinates'],
            'steps': steps,
        })

    except Exception as e:
        return Response({'detail': f'Ошибка при построении маршрута: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TariffPlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TariffPlan.objects.filter(is_active=True)
    serializer_class = TariffPlanSerializer
    permission_classes = [permissions.AllowAny]


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_payment(request):
    serializer = CreatePaymentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    plan = TariffPlan.objects.get(id=serializer.validated_data['plan_id'])

    subscription = UserSubscription.objects.create(
        user=request.user,
        plan=plan,
        status='pending',
    )

    from .payment_service import payment_service
    result = payment_service.create_invoice(
        user=request.user,
        amount=plan.price,
        description=f'Подписка {plan.display_name} - CareerHub',
        subscription_id=subscription.id,
    )

    if not result['success']:
        subscription.delete()
        return Response(
            {'detail': f'Ошибка создания платежа: {result.get("error", "Неизвестная ошибка")}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    Payment.objects.create(
        user=request.user,
        subscription=subscription,
        invoice_no=result['invoice_no'],
        amount=plan.price,
        status='pending',
    )

    return Response({
        'invoice_no': result['invoice_no'],
        'redirect_url': result['redirect_url'],
        'subscription_id': subscription.id,
    })


@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def payment_webhook(request):
    data = request.data

    from .payment_service import payment_service
    if not payment_service.verify_webhook_signature(data):
        return Response({'detail': 'Invalid signature'}, status=status.HTTP_403_FORBIDDEN)

    invoice_no = data.get('InvoiceNo')
    express_status = data.get('Status')

    if not invoice_no:
        return Response({'detail': 'InvoiceNo required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        payment = Payment.objects.select_related('subscription', 'subscription__plan', 'user').get(invoice_no=invoice_no)
    except Payment.DoesNotExist:
        return Response({'detail': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)

    if payment.status == 'paid':
        return Response({'detail': 'Already processed'})

    status_map = {
        1: 'pending',
        2: 'failed',
        3: 'paid',
        4: 'paid',
        5: 'cancelled',
        6: 'paid',
        7: 'cancelled',
    }

    new_status = status_map.get(express_status, 'failed')
    payment.status = new_status
    payment.payment_method = data.get('PaymentMethod', '')

    if new_status == 'paid':
        from django.utils import timezone
        from datetime import timedelta

        payment.paid_at = timezone.now()
        payment.save()

        subscription = payment.subscription
        subscription.status = 'active'
        subscription.started_at = timezone.now()
        subscription.expires_at = timezone.now() + timedelta(days=subscription.plan.duration_days)
        subscription.save()

        payment.user.current_plan = subscription.plan.name
        payment.user.save()

        Notification.objects.create(
            user=payment.user,
            notification_type='system',
            title='Подписка активирована!',
            message=f'Ваш тариф "{subscription.plan.display_name}" успешно активирован до {subscription.expires_at.strftime("%d.%m.%Y")}.',
            link='/settings/billing',
        )

        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'user_{payment.user.id}',
                {
                    'type': 'send_notification',
                    'notification_type': 'system',
                    'title': 'Подписка активирована!',
                    'message': f'Ваш тариф "{subscription.plan.display_name}" активирован.',
                    'data': {'link': '/settings/billing'},
                }
            )
        except Exception:
            pass
    else:
        payment.save()
        if new_status in ('failed', 'cancelled'):
            payment.subscription.status = new_status
            payment.subscription.save()

    return Response({'detail': 'OK'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_subscription(request):
    subscription = request.user.get_subscription()
    if subscription:
        serializer = UserSubscriptionSerializer(subscription)
        return Response(serializer.data)
    return Response({'detail': 'Нет активной подписки.', 'current_plan': request.user.current_plan})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def payment_history(request):
    payments = Payment.objects.filter(user=request.user)
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_plan_access(request):
    plan = request.user.current_plan
    features = {
        'current_plan': plan,
        'unlimited_jobs': plan in ('professional', 'corporate'),
        'advanced_search': plan in ('professional', 'corporate'),
        'priority_listing': plan in ('professional', 'corporate'),
        'analytics': plan in ('professional', 'corporate'),
        'highlighting': plan in ('professional', 'corporate'),
        'priority_support': plan in ('professional', 'corporate'),
        'api_access': plan == 'corporate',
        'personal_manager': plan == 'corporate',
        'custom_branding': plan == 'corporate',
        'hr_integration': plan == 'corporate',
    }

    subscription = request.user.get_subscription()
    if subscription:
        features['expires_at'] = subscription.expires_at
        features['plan_name'] = subscription.plan.display_name

    return Response(features)


@csrf_exempt
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def google_auth_redirect(request):
    import secrets
    from urllib.parse import urlencode

    state = secrets.token_urlsafe(32)
    request.session['google_oauth_state'] = state

    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'prompt': 'consent',
        'state': state,
    }
    google_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(params)
    return HttpResponseRedirect(google_url)


@csrf_exempt
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def google_auth_callback(request):
    import uuid as uuid_mod
    code = request.query_params.get('code')
    state = request.query_params.get('state')
    error = request.query_params.get('error')

    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')

    if error:
        return HttpResponseRedirect(f'{frontend_url}/auth/login?error=google_denied')

    if not code:
        return HttpResponseRedirect(f'{frontend_url}/auth/login?error=no_code')

    expected_state = request.session.get('google_oauth_state')
    if not expected_state or not state or state != expected_state:
        return HttpResponseRedirect(f'{frontend_url}/auth/login?error=invalid_state')

    del request.session['google_oauth_state']

    token_data = {
        'code': code,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'grant_type': 'authorization_code',
    }

    try:
        token_response = http_requests.post('https://oauth2.googleapis.com/token', data=token_data, timeout=10)
        token_json = token_response.json()

        if 'access_token' not in token_json:
            return HttpResponseRedirect(f'{frontend_url}/auth/login?error=token_exchange_failed')

        access_token = token_json['access_token']

        userinfo_response = http_requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10,
        )
        userinfo = userinfo_response.json()

        email = userinfo.get('email')
        name = userinfo.get('name', '')
        avatar_url = userinfo.get('picture', '')

        if not email:
            return HttpResponseRedirect(f'{frontend_url}/auth/login?error=no_email')

        user = None
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            username = email.split('@')[0]
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f'{base_username}{counter}'
                counter += 1

            random_password = uuid_mod.uuid4().hex
            user = User.objects.create_user(
                username=username,
                email=email,
                password=random_password,
                first_name=name.split(' ')[0] if name else '',
                last_name=' '.join(name.split(' ')[1:]) if name and ' ' in name else '',
                role='student',
                is_email_verified=True,
            )

            if avatar_url:
                try:
                    avatar_response = http_requests.get(avatar_url, timeout=10)
                    if avatar_response.status_code == 200:
                        from django.core.files.base import ContentFile
                        ext = 'jpg'
                        user.avatar.save(f'avatars/{uuid_mod.uuid4()}.{ext}', ContentFile(avatar_response.content), save=True)
                except Exception:
                    pass

        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)

        redirect_url = (
            f'{frontend_url}/auth/callback'
            f'?access={str(refresh.access_token)}'
            f'&refresh={str(refresh)}'
        )
        return HttpResponseRedirect(redirect_url)

    except http_requests.exceptions.RequestException:
        return HttpResponseRedirect(f'{frontend_url}/auth/login?error=google_api_error')
    except Exception:
        return HttpResponseRedirect(f'{frontend_url}/auth/login?error=server_error')