from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.BlogPostListView.as_view(), name='blogpost_list'),
    path('create/', views.BlogPostCreateView.as_view(), name='blogpost_create'),

    # CRUD
    path('<int:pk>/update/', views.BlogPostUpdateView.as_view(), name='blogpost_update'),
    path('<int:pk>/delete/', views.BlogPostDeleteView.as_view(), name='blogpost_delete'),

    # Переключение публикации (только для контент-менеджеров)
    path('<int:pk>/toggle-publish/', views.BlogPostTogglePublishView.as_view(), name='blogpost_toggle_publish'),

    # Детальная — в конце
    path('<int:pk>/', views.BlogPostDetailView.as_view(), name='blogpost_detail'),
]
