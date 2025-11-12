from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # News
    path('news/', views.news_list, name='news_list'),
    path('news/<int:pk>/', views.news_detail, name='news_detail'),

    # Events
    path('events/', views.events_list, name='events_list'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
]
