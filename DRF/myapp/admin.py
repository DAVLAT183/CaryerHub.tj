from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, StudentProfile, EmployerProfile,
    Category, Resume, Job, Application, Favorite,
    WorkSchedule, WorkFormat, WorkExperience, Notification,
    TariffPlan, UserSubscription, Payment
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'current_plan', 'is_staff']
    list_filter = ['role', 'is_staff', 'current_plan']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('role', 'phone', 'avatar', 'current_plan')}),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'university', 'faculty', 'course', 'city']
    list_filter = ['city', 'university']


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'user', 'is_verified', 'website']
    list_filter = ['is_verified']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['title', 'student', 'schedule_type', 'work_format', 'github_url', 'portfolio_url', 'linkedin_url', 'created_at']
    list_filter = ['schedule_type', 'work_format']


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'employer', 'category', 'salary_min', 'salary_max', 'is_active', 'created_at']
    list_filter = ['is_active', 'category', 'schedule', 'work_format']


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['job', 'resume', 'status', 'created_at']
    list_filter = ['status']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['student', 'job', 'created_at']


@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(WorkFormat)
class WorkFormatAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']


@admin.register(TariffPlan)
class TariffPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'price', 'duration_days', 'is_active']
    list_filter = ['is_active']


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'started_at', 'expires_at', 'created_at']
    list_filter = ['status', 'plan']
    search_fields = ['user__username', 'user__email']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'invoice_no', 'amount', 'status', 'payment_method', 'paid_at', 'created_at']
    list_filter = ['status', 'payment_method']
    search_fields = ['user__username', 'invoice_no']
