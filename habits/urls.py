from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views


router = DefaultRouter()
router.register(r'habits', views.HabitViewSet)

urlpatterns = [
    path('api/users/register/', views.RegisterView.as_view(), name='register'),
    path('api/token/obtain/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include(router.urls)),
]

# (Для jwt_views нужен импорт: from rest_framework_simplejwt import views as jwt_views)

# Итоговые пути:

# text
# /api/users/register/          → POST (Create, AllowAny)
# /api/token/obtain/            → POST (username + password → access + refresh)
# /api/token/refresh/           → POST (refresh → new access)
# /api/habits/                  → GET / POST (свои, 5/стр, пагинация)
# /api/habits/{id}/             → GET / PUT / PATCH / DELETE (владелец)
# /api/habits/public/           → GET (все is_public=True, 5/стр, только чтение)
