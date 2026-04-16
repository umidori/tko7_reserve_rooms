from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import home

urlpatterns = [
    path('', login_required(home), name='home'),
]
