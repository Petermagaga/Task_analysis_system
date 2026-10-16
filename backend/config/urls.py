
from django.contrib import admin
from django.urls import path,include

from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView)

urlpatterns = [
    path('admin/', admin.site.urls),

    #Authentication
    path("api/auth/token/",TokenObtainPairView.as_view(),name="token_obtain_pair"),
    path("api/auth/token/refresh/",TokenRefreshView.as_view(),name="token_refresh"),

    #work items
    path("api/work-items/",include("work_items.urls")),
]

