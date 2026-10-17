from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View
)

from .models import Product, Category, News, Contact
from .forms import ProductForm


# ============================================================
# Миксин для проверки прав на управление товаром
# ============================================================

class ProductPermissionMixin:
    """Миксин для вьюх редактирования/удаления товара.

    Проверяет, что пользователь может управлять объектом:
    - владелец товара;
    - модератор (право can_unpublish_product);
    - суперюзер.

    Если прав нет — отдаём 403.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        self.object = self.get_object()

        if not self.object.can_be_managed_by(request.user):
            raise PermissionDenied('У вас нет прав на управление этим товаром.')

        return super().dispatch(request, *args, **kwargs)


# ============================================================
# Главная страница
# ============================================================

class HomeView(ListView):
    """Главная страница: список товаров с пагинацией + новости.

    Логика отображения:
    - аноним и обычный юзер — только опубликованные товары;
    - модератор — все товары (включая неопубликованные);
    - владелец — свои товары (включая неопубликованные) + все опубликованные.
    """

    model = Product
    template_name = 'home.html'
    paginate_by = 6

    def get_queryset(self):
        qs = Product.objects.select_related('category', 'owner')

        user = self.request.user

        if not user.is_authenticated:
            return qs.filter(is_published=True)

        if user.is_superuser or user.is_moderator:
            return qs

        return qs.filter(Q(is_published=True) | Q(owner=user))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['news'] = News.objects.order_by('-date')[:6]
        return context


# ============================================================
# Категория
# ============================================================

class CategoryDetailView(DetailView):
    """Страница категории с товарами."""

    model = Category
    template_name = 'category_detail.html'
    context_object_name = 'category'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Показываем только товары в наличии и опубликованные
        context['products'] = self.object.products.filter(
            in_stock=True, is_published=True,
        )
        return context


# ============================================================
# Товар
# ============================================================

class ProductDetailView(DetailView):
    """Детальная страница товара. Общедоступна, но черновики — только своим.

    Логика queryset:
    - аноним и обычный юзер — только опубликованные товары;
    - модератор и суперюзер — все;
    - владелец — свои (включая черновики) + опубликованные чужие.

    Чужой черновик по прямой ссылке → 404 (объект «не существует»).
    """

    model = Product
    template_name = 'product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        # Аноним — только опубликованные
        if not user.is_authenticated:
            return qs.filter(is_published=True)

        # Модератор или суперюзер — все
        if user.is_superuser or user.is_moderator:
            return qs

        # Владелец — свои (любые) + опубликованные чужие
        return qs.filter(Q(is_published=True) | Q(owner=user))


class ProductCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Форма добавления товара. Только для авторизованных.

    Автоматически привязывает товар к текущему пользователю (owner).
    """

    model = Product
    form_class = ProductForm
    template_name = 'product_form.html'
    success_message = 'Товар «%(name)s» добавлен!'

    def form_valid(self, form):
        product = form.save(commit=False)

        # По критерию: owner заполняется автоматом из request.user
        product.owner = self.request.user

        # Генерируем уникальный slug из name
        base_slug = slugify(product.name, allow_unicode=True)
        slug = base_slug
        counter = 1
        while Product.objects.filter(slug=slug).exists():
            counter += 1
            slug = f'{base_slug}-{counter}'
        product.slug = slug

        product.save()
        self.object = product
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('catalog:product_detail', kwargs={'pk': self.object.pk})


class ProductUpdateView(LoginRequiredMixin, ProductPermissionMixin, UpdateView):
    """Редактирование товара. Доступно владельцу, модератору, суперюзеру."""

    model = Product
    form_class = ProductForm
    template_name = 'product_form.html'

    def get_success_url(self):
        return reverse_lazy('catalog:product_detail', kwargs={'pk': self.object.pk})


class ProductDeleteView(LoginRequiredMixin, ProductPermissionMixin, DeleteView):
    """Удаление товара. Доступно владельцу, модератору, суперюзеру."""

    model = Product
    template_name = 'product_confirm_delete.html'
    context_object_name = 'product'
    success_url = reverse_lazy('catalog:home')


class ProductTogglePublishView(LoginRequiredMixin, View):
    """Переключение статуса публикации товара. Только модератор/суперюзер."""

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)

        if not product.can_be_unpublished_by(request.user):
            raise PermissionDenied('У вас нет прав на изменение публикации.')

        product.is_published = not product.is_published
        product.save(update_fields=['is_published', 'updated_at'])

        if product.is_published:
            messages.success(request, f'Товар «{product.name}» опубликован.')
        else:
            messages.warning(request, f'Товар «{product.name}» снят с публикации.')

        return redirect('catalog:product_detail', pk=product.pk)


# ============================================================
# Контакты
# ============================================================

class ContactsView(TemplateView):
    """Страница контактов: форма обратной связи + данные из модели Contact."""

    template_name = 'contacts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contact_info'] = Contact.objects.first()
        return context

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        print(f"Имя: {name}, Email: {email}, Сообщение: {message}")
        messages.success(request, 'Спасибо! Ваше сообщение отправлено.')
        return redirect('catalog:contacts')
