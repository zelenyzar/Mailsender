from django.urls import path, include
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    path('api/users/', include('users.urls')),
    path('api/token/obtain/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('habits.urls')),
]

# Пути:

# text
# POST /api/users/register/      → AllowAny, создание пользователя
# POST /api/token/obtain/        → JWT (simplejwt)
# POST /api/token/refresh/        → JWT
