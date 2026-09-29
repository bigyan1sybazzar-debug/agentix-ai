from django.urls import path
from . import views

urlpatterns = [
    # Dashboard (main entry point)
    path("", views.dashboard_view, name="dashboard"),

    # Registration (risk evaluation & progressive profiling)
    path("registration/", views.registration_view, name="registration"),
]
