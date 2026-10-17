from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.cache import cache
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
from .services.products import get_products_by_category


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
    """Страница категории с товарами.

    Товары берём через сервис get_products_by_category — он кэширует
    результат в Redis по ключу `category_{id}` с TTL 300 секунд.
    """

    model = Category
    template_name = 'category_detail.html'
    context_object_name = 'category'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = get_products_by_category(self.object.id)
        return context


# ============================================================
# Товар
# ============================================================

class ProductDetailView(DetailView):
    """Детальная страница товара. Общедоступна, но черновики — только своим.

    Логика:
    - аноним и обычный юзер — только опубликованные (кэшируются);
    - модератор и суперюзер — все (без кэша);
    - владелец — свои (включая черновики) + опубликованные чужие (без кэша).

    Чужой черновик по прямой ссылке → 404.
    """

    model = Product
    template_name = 'product_detail.html'
    context_object_name = 'product'

    # TTL кэша детальной страницы — 5 минут
    PRODUCT_CACHE_TTL = 300

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return qs.filter(is_published=True)

        if user.is_superuser or user.is_moderator:
            return qs

        return qs.filter(Q(is_published=True) | Q(owner=user))

    def get_object(self, queryset=None):
        """Достаём товар с учётом прав.

        Кэшируем только для анонимов и только опубликованные товары.
        """
        user = self.request.user
        pk = self.kwargs.get(self.pk_url_kwarg or 'pk')

        # 1. Пытаемся взять из кэша — только для анонима
        if not user.is_authenticated:
            cache_key = f'product_detail_{pk}'
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        # 2. Идём в БД с фильтром по правам
        qs = self.get_queryset()
        obj = get_object_or_404(qs, pk=pk)

        # 3. Кэшируем только опубликованный товар и только для анонима
        if not user.is_authenticated and obj.is_published:
            cache.set(f'product_detail_{pk}', obj, timeout=self.PRODUCT_CACHE_TTL)

        return obj


class ProductCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Форма добавления товара. Только для авторизованных."""

    model = Product
    form_class = ProductForm
    template_name = 'product_form.html'
    success_message = 'Товар «%(name)s» добавлен!'

    def form_valid(self, form):
        product = form.save(commit=False)

        product.owner = self.request.user

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
