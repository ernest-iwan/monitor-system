from django.urls import path
from . import views

urlpatterns = [
    path('status/<slug>', views.status, name='status'),
]