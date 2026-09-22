from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    StudentProfile, EmployerProfile,
    Category, Resume, Job, Application, Favorite,
    ChatSession, ChatMessage, EmailVerification, DirectMessage,
    WorkSchedule, WorkFormat, WorkExperience, Notification,
    TariffPlan, UserSubscription, Payment
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    student_profile_id = serializers.SerializerMethodField()
    employer_profile_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'phone', 'avatar', 'location', 'student_profile_id', 'employer_profile_id',
        ]
        read_only_fields = ['id']

    def get_student_profile_id(self, obj):
        if hasattr(obj, 'student_profile'):
            return obj.student_profile.id
        return None

    def get_employer_profile_id(self, obj):
        if hasattr(obj, 'employer_profile'):
            return obj.employer_profile.id
        return None


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'phone', 'location']
        read_only_fields = ['id']

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Пользователь с таким именем уже существует.')
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует.')
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        if user.role == 'student':
            StudentProfile.objects.create(user=user)
        elif user.role == 'employer':
            EmployerProfile.objects.create(user=user, company_name='')
        return user


class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = StudentProfile
        fields = ['id', 'user', 'university', 'faculty', 'course', 'birth_date', 'age', 'city']


class EmployerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = EmployerProfile
        fields = ['id', 'user', 'company_name', 'description', 'website', 'address', 'is_verified']
        read_only_fields = ['is_verified']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class CategoryWithCountSerializer(serializers.ModelSerializer):
    jobs_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'jobs_count']

    def get_jobs_count(self, obj):
        return obj.jobs.filter(is_active=True).count()


class WorkScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkSchedule
        fields = ['id', 'name', 'slug']


class WorkFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkFormat
        fields = ['id', 'name', 'slug']


class WorkExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkExperience
        fields = ['id', 'name', 'slug']


class ResumeSerializer(serializers.ModelSerializer):
    student = StudentProfileSerializer(read_only=True)

    class Meta:
        model = Resume
        fields = [
            'id', 'student', 'title', 'about', 'skills',
            'schedule_type', 'work_format',
            'github_url', 'portfolio_url', 'linkedin_url',
            'style',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ResumeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id', 'title', 'about', 'skills', 'schedule_type', 'work_format', 'github_url', 'portfolio_url', 'linkedin_url', 'style']

    def create(self, validated_data):
        validated_data['student'] = self.context['request'].user.student_profile
        return super().create(validated_data)


class JobSerializer(serializers.ModelSerializer):
    employer = EmployerProfileSerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    applications_count = serializers.IntegerField(read_only=True, default=0)
    is_favorited = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    has_location = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id', 'employer', 'category', 'category_name', 'title', 'description',
            'salary_min', 'salary_max', 'min_age', 'schedule', 'work_format',
            'experience_required', 'is_active', 'created_at', 'applications_count',
            'is_favorited',
            'image', 'image_url', 'location_lat', 'location_lng', 'location_address', 'has_location',
            'source', 'source_url', 'source_id',
        ]
        read_only_fields = ['id', 'created_at']

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and hasattr(request.user, 'student_profile'):
            return Favorite.objects.filter(
                student=request.user.student_profile, job=obj
            ).exists()
        return False

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def get_has_location(self, obj):
        return obj.has_location()


class JobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            'id', 'category', 'title', 'description',
            'salary_min', 'salary_max', 'min_age', 'schedule', 'work_format',
            'experience_required',
            'image', 'location_lat', 'location_lng', 'location_address',
        ]

    def validate(self, data):
        if data.get('salary_min') and data.get('salary_max'):
            if data['salary_min'] > data['salary_max']:
                raise serializers.ValidationError('Минимальная зарплата не может быть больше максимальной.')
        return data

    def create(self, validated_data):
        validated_data['employer'] = self.context['request'].user.employer_profile
        return super().create(validated_data)


class ApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    student_name = serializers.CharField(source='resume.student.user.username', read_only=True)
    job_employer_name = serializers.CharField(source='job.employer.company_name', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'job', 'job_title', 'job_employer_name', 'resume', 'student_name',
            'status', 'cover_letter', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'created_at']


class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['id', 'job', 'resume', 'cover_letter']

    def validate(self, data):
        request = self.context['request']
        try:
            student_profile = request.user.student_profile
        except Exception:
            raise serializers.ValidationError('Профиль студента не найден.')
        if data['resume'].student != student_profile:
            raise serializers.ValidationError('Вы можете откликаться только своим резюме.')
        if Application.objects.filter(job=data['job'], resume=data['resume']).exists():
            raise serializers.ValidationError('Вы уже откликнулись на эту вакансию.')
        return data

    def create(self, validated_data):
        return super().create(validated_data)


class FavoriteSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    job_id = serializers.PrimaryKeyRelatedField(
        queryset=Job.objects.all(), source='job', write_only=True
    )

    class Meta:
        model = Favorite
        fields = ['id', 'job', 'job_id', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        validated_data['student'] = self.context['request'].user.student_profile
        return super().create(validated_data)


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'created_at']
        read_only_fields = ['id', 'role', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'messages', 'last_message', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        last = obj.messages.last()
        if last:
            return ChatMessageSerializer(last).data
        return None


class ChatSessionListSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    messages_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'last_message', 'messages_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        last = obj.messages.last()
        if last:
            return {'role': last.role, 'content': last.content[:100]}
        return None

    def get_messages_count(self, obj):
        return obj.messages.count()


class DirectMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    recipient_name = serializers.CharField(source='recipient.username', read_only=True)

    class Meta:
        model = DirectMessage
        fields = ['id', 'sender', 'sender_name', 'recipient', 'recipient_name', 'content', 'created_at', 'is_read']
        read_only_fields = ['id', 'sender', 'created_at', 'is_read']


class ConversationSerializer(serializers.Serializer):
    user = UserSerializer(read_only=True)
    last_message = DirectMessageSerializer(read_only=True)
    unread_count = serializers.IntegerField(read_only=True)


class NotificationSerializer(serializers.ModelSerializer):
    employer_avatar = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message', 'link', 'is_read', 'created_at', 'employer_avatar']
        read_only_fields = ['id', 'created_at']

    def get_employer_avatar(self, obj):
        if obj.notification_type.startswith('application_'):
            request = self.context.get('request')
            try:
                app = obj.link.split('/applications/')[1].split('/')[0] if '/applications/' in obj.link else None
            except (IndexError, AttributeError):
                app = None
            if app:
                try:
                    application = Application.objects.select_related('job__employer__user').get(id=int(app))
                    avatar = application.job.employer.user.avatar
                    if avatar and request:
                        return request.build_absolute_uri(avatar.url)
                    return None
                except (Application.DoesNotExist, ValueError):
                    pass
        return None


class TariffPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TariffPlan
        fields = ['id', 'name', 'display_name', 'price', 'duration_days', 'features']


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = TariffPlanSerializer(read_only=True)

    class Meta:
        model = UserSubscription
        fields = ['id', 'plan', 'status', 'started_at', 'expires_at', 'created_at']
        read_only_fields = ['id', 'status', 'started_at', 'expires_at', 'created_at']


class PaymentSerializer(serializers.ModelSerializer):
    subscription_plan = serializers.CharField(source='subscription.plan.display_name', read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'invoice_no', 'amount', 'status', 'payment_method', 'paid_at', 'created_at', 'subscription_plan']
        read_only_fields = ['id', 'invoice_no', 'amount', 'status', 'payment_method', 'paid_at', 'created_at']


class CreatePaymentSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()

    def validate_plan_id(self, value):
        try:
            plan = TariffPlan.objects.get(id=value, is_active=True, price__gt=0)
        except TariffPlan.DoesNotExist:
            raise serializers.ValidationError('Тарифный план не найден или бесплатный.')
        return value
