from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('products/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('contacts/', views.ContactsView.as_view(), name='contacts'),
]
