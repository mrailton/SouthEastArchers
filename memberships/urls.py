from django.urls import path
from . import views

app_name = 'memberships'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('credits/purchase/', views.purchase_credits, name='purchase_credits'),
    path('profile/', views.profile, name='profile'),
]
