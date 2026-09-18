from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.home, name='home'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('products/create/', views.product_create, name='product_create'),   # <-- добавили
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('contacts/', views.contacts, name='contacts'),
]
