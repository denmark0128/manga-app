from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.home, name='about'),
    path('contact/', views.home, name='contact'),
    path('series/', views.home, name='series'),
    path('upload/', views.home, name='upload'),
    path('series/<int:series_id>/', views.home, name='series_detail'),
]
