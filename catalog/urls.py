from django.urls import path

from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),

    # CRUD товаров
    path('products/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/update/', views.ProductUpdateView.as_view(), name='product_update'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),

    # Переключение публикации (только для модераторов)
    path('products/<int:pk>/toggle-publish/', views.ProductTogglePublishView.as_view(), name='product_toggle_publish'),

    # Детальная — в конце, чтобы не перекрывала другие маршруты
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),

    path('contacts/', views.ContactsView.as_view(), name='contacts'),
]
