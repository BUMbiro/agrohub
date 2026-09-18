from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils.text import slugify

from .models import Product, Category, News, Contact
from .forms import ProductForm


def home(request):
    """Главная страница: список товаров (с пагинацией), новости + вывод 5 последних в консоль."""
    news = News.objects.order_by('-date')[:6]
    products_qs = Product.objects.all()

    # --- Пагинация: 6 товаров на страницу ---
    paginator = Paginator(products_qs, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # -----------------------------------------

    # --- Доп. задание из прошлой домашки: 5 последних продуктов в консоль ---
    latest_products = Product.objects.order_by('-created_at')[:5]
    print('Последние 5 продуктов:')
    for p in latest_products:
        print(f'  - {p.name} ({p.price} ₽)')
    # ----------------------------------------------------------------------

    return render(request, 'home.html', {
        'news': news,
        'page_obj': page_obj,   # для пагинации
    })


def category_detail(request, slug):
    """Страница категории с товарами."""
    category = get_object_or_404(Category, slug=slug)
    products = category.products.filter(in_stock=True)
    return render(request, 'category_detail.html', {
        'category': category,
        'products': products,
    })


def product_detail(request, pk):
    """Детальная страница товара. Получает pk, извлекает объект через ORM."""
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'product_detail.html', {'product': product})


def product_create(request):
    """Форма добавления нового товара. GET — показать, POST — валидировать и сохранить."""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            # Slug генерируется из name. Если такой slug уже есть — добавим суффикс с id
            base_slug = slugify(product.name, allow_unicode=True)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                counter += 1
                slug = f'{base_slug}-{counter}'
            product.slug = slug
            product.save()
            messages.success(request, f'Товар «{product.name}» добавлен!')
            return redirect('catalog:product_detail', pk=product.pk)
    else:
        form = ProductForm()

    return render(request, 'product_form.html', {'form': form})


def contacts(request):
    """Страница контактов: форма обратной связи + данные из модели Contact."""
    contact_info = Contact.objects.first()

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        print(f"Имя: {name}, Email: {email}, Сообщение: {message}")
        messages.success(request, 'Спасибо! Ваше сообщение отправлено.')
        return render(request, 'contacts.html', {'contact_info': contact_info})

    return render(request, 'contacts.html', {'contact_info': contact_info})
