from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from .models import Product, Category, News, Contact


def home(request):
    """Главная страница: категории, новости + вывод 5 последних продуктов в консоль."""
    categories = Category.objects.all()
    news = News.objects.order_by('-date')[:6]

    # --- Доп. задание: последние 5 созданных продуктов в консоль ---
    latest_products = Product.objects.order_by('-created_at')[:5]
    print('Последние 5 продуктов:')
    for p in latest_products:
        print(f'  - {p.name} ({p.price} ₽)')
    # ---------------------------------------------------------------

    return render(request, 'home.html', {
        'categories': categories,
        'news': news,
    })


def category_detail(request, slug):
    """Страница категории с товарами."""
    category = get_object_or_404(Category, slug=slug)
    products = category.products.filter(in_stock=True)
    return render(request, 'category_detail.html', {
        'category': category,
        'products': products,
    })


def product_detail(request, slug):
    """Детальная страница товара."""
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'product_detail.html', {'product': product})


def contacts(request):
    """Страница контактов: форма обратной связи + данные из модели Contact."""
    # Берём первый контакт из БД (обычно он один)
    contact_info = Contact.objects.first()

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        print(f"Имя: {name}, Email: {email}, Сообщение: {message}")
        messages.success(request, 'Спасибо! Ваше сообщение отправлено.')
        return render(request, 'contacts.html', {'contact_info': contact_info})

    return render(request, 'contacts.html', {'contact_info': contact_info})
