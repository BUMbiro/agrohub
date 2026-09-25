from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.text import slugify
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.urls import reverse_lazy
from django.shortcuts import redirect

from .models import Product, Category, News, Contact
from .forms import ProductForm


class HomeView(ListView):
    """Главная страница: список товаров с пагинацией + новости."""

    model = Product
    template_name = 'home.html'
    context_object_name = 'page_obj'      # сохраняем имя переменной для шаблона
    paginate_by = 6                        # 6 товаров на страницу

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Новости отдельным запросом
        context['news'] = News.objects.order_by('-date')[:6]

        # Доп. задание из первой домашки: 5 последних продуктов в консоль
        latest_products = Product.objects.order_by('-created_at')[:5]
        print('Последние 5 продуктов:')
        for p in latest_products:
            print(f'  - {p.name} ({p.price} ₽)')

        return context


class CategoryDetailView(DetailView):
    """Страница категории с товарами."""

    model = Category
    template_name = 'category_detail.html'
    context_object_name = 'category'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем товары этой категории (только в наличии)
        context['products'] = self.object.products.filter(in_stock=True)
        return context


class ProductDetailView(DetailView):
    """Детальная страница товара. Работает по pk."""

    model = Product
    template_name = 'product_detail.html'
    context_object_name = 'product'


class ProductCreateView(SuccessMessageMixin, CreateView):
    """Форма добавления товара. После сохранения — на страницу нового товара."""

    model = Product
    form_class = ProductForm
    template_name = 'product_form.html'
    success_message = 'Товар «%(name)s» добавлен!'

    def form_valid(self, form):
        """Генерируем slug из name перед сохранением."""
        product = form.save(commit=False)
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
        """Редирект на страницу нового товара."""
        return reverse_lazy('catalog:product_detail', kwargs={'pk': self.object.pk})


class ContactsView(TemplateView):
    """Страница контактов: форма обратной связи + данные из модели Contact."""

    template_name = 'contacts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contact_info'] = Contact.objects.first()
        return context

    def post(self, request, *args, **kwargs):
        """Обработка POST-запроса от формы обратной связи."""
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        print(f"Имя: {name}, Email: {email}, Сообщение: {message}")
        messages.success(request, 'Спасибо! Ваше сообщение отправлено.')
        return redirect('catalog:contacts')
