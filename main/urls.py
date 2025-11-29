from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.home, name='about'),
    path('contact/', views.home, name='contact'),
    path('paper/', views.home, name='paper'),
    path('upload/', views.home, name='upload'),
    path('paper/<int:paper_id>/', views.home, name='paper_detail'),
]
