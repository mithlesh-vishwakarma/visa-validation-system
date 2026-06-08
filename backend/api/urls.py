from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from authentication.views import RegisterView, UserProfileView, OrganizationUsersViewSet
from clients.views import ClientViewSet
from rules_engine.views import CountryRuleViewSet
from submissions.views import SubmissionViewSet, DocumentViewSet, ActivityLogViewSet, DashboardAnalyticsAPI

router = DefaultRouter()
router.register(r'org-users', OrganizationUsersViewSet, basename='org-users')
router.register(r'clients', ClientViewSet, basename='clients')
router.register(r'country-rules', CountryRuleViewSet, basename='country-rules')
router.register(r'submissions', SubmissionViewSet, basename='submissions')
router.register(r'documents', DocumentViewSet, basename='documents')
router.register(r'activity-logs', ActivityLogViewSet, basename='activity-logs')

urlpatterns = [
    # Auth
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/profile/', UserProfileView.as_view(), name='profile'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Dashboard Analytics
    path('dashboard/analytics/', DashboardAnalyticsAPI.as_view(), name='dashboard-analytics'),
    
    # Router endpoints
    path('', include(router.urls)),
]
