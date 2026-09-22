from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet,basename="Users")
router.register(r'student-profiles', views.StudentProfileViewSet,basename="Students-profiles")
router.register(r'employer-profiles', views.EmployerProfileViewSet,basename="employer-profiles")
router.register(r'categories', views.CategoryViewSet,basename="categories")
router.register(r'work-schedules', views.WorkScheduleViewSet,basename="work-schedules")
router.register(r'work-formats', views.WorkFormatViewSet,basename="work-formats")
router.register(r'work-experiences', views.WorkExperienceViewSet,basename="work-experiences")
router.register(r'resumes', views.ResumeViewSet,basename="resumes")
router.register(r'jobs', views.JobViewSet,basename="jobs")
router.register(r'applications', views.ApplicationViewSet,basename="applications")
router.register(r'favorites', views.FavoriteViewSet,basename="favorites")
router.register(r'chat/sessions', views.ChatSessionViewSet,basename="chat-sessions")
router.register(r'notifications', views.NotificationViewSet,basename="notifications")
router.register(r'tariffs', views.TariffPlanViewSet, basename="tariffs")

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('favorites/add/', views.add_to_favorites, name='add-to-favorites'),
    path('favorites/<int:job_id>/remove/', views.remove_from_favorites, name='remove-from-favorites'),
    path('ai/generate-resume/', views.ai_generate_resume, name='ai-generate-resume'),
    path('ai/create-resume/', views.ai_create_resume, name='ai-create-resume'),
    path('ai/resume-chat/', views.ai_resume_chat, name='ai-resume-chat'),
    path('ai/recommend-jobs/', views.ai_recommend_jobs, name='ai-recommend-jobs'),
    path('chat/send/', views.chat_send_message, name='chat-send-message'),
    path('chat/<int:session_id>/messages/', views.chat_session_messages, name='chat-session-messages'),
    path('messages/conversations/', views.conversations_list, name='conversations-list'),
    path('messages/<int:user_id>/', views.direct_messages, name='direct-messages'),
    path('messages/employers/', views.employer_chat_users, name='employer-chat-users'),
    path('auth/send-verification/', views.send_verification_email, name='send-verification'),
    path('auth/verify-email/', views.verify_email, name='verify-email'),
    path('auth/check-verification/', views.check_email_verification, name='check-verification'),
    path('auth/password-reset/', views.password_reset_request, name='password-reset-request'),
    path('auth/password-reset/confirm/', views.password_reset_confirm, name='password-reset-confirm'),
    path('parsing/somon-tj/', views.parse_somon_tj, name='parse-somon-tj'),
    path('jobs/<int:job_id>/pdf/', views.generate_job_pdf, name='generate-job-pdf'),
    path('resumes/<int:resume_id>/pdf/', views.generate_resume_pdf, name='generate-resume-pdf'),
    path('route/', views.calculate_route, name='calculate-route'),
    path('payments/create/', views.create_payment, name='create-payment'),
    path('payments/webhook/', views.payment_webhook, name='payment-webhook'),
    path('payments/my-subscription/', views.my_subscription, name='my-subscription'),
    path('payments/history/', views.payment_history, name='payment-history'),
    path('payments/check-access/', views.check_plan_access, name='check-plan-access'),
    path('auth/google/', views.google_auth_redirect, name='google-auth-redirect'),
    path('auth/google/callback/', views.google_auth_callback, name='google-auth-callback'),
    path('', include(router.urls)),
]
