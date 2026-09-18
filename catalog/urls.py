from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.home, name='home'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),  # было product/<slug:slug>/
    path('contacts/', views.contacts, name='contacts'),
]
