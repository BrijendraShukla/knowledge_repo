from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (LoginViewSet)

router = DefaultRouter()
router.register("login", LoginViewSet, basename="login")
urlpatterns = [
    path("", include(router.urls)),
]
