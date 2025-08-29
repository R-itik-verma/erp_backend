from django.http import JsonResponse
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

def home(request):
    return JsonResponse({"message": "ERP Backend is running"})

urlpatterns = [
    path('', home),  # Root URL
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('erp.urls')),
]
