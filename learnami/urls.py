from django.urls import path
from . import views

urlpatterns = [
    # Registration (risk evaluation & progressive profiling)
    path("", views.registration_view, name="registration"),
]
