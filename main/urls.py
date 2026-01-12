from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('upload/', views.upload, name='upload'),
    path('paper/', views.paper, name='paper'),
    path('author/', views.author_list, name='author_list'),
    path('series/', views.series_list, name='series_list'),
    path('series/<int:series_id>/', views.series_detail, name='series_detail'),
    path('series/<int:series_id>/content/', views.series_detail_content, name='series_detail_content'),
    path('author/<int:author_id>/', views.author_detail, name='author_detail'),
    path('author/<int:author_id>/content/', views.author_detail_content, name='author_detail_content'),
    path('toggle-nsfw/', views.toggle_nsfw, name='toggle_nsfw'),
]
