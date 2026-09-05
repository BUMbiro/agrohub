from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from .models import Product, Category, News

def home(request):
    categories = Category.objects.all()
    news = News.objects.order_by('-date')[:6]
    return render(request, 'home.html', {'categories': categories, 'news': news})

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.filter(in_stock=True)
    return render(request, 'category_detail.html', {'category': category, 'products': products})

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'product_detail.html', {'product': product})

def contacts(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        print(f"Имя: {name}, Email: {email}, Сообщение: {message}")
        messages.success(request, 'Спасибо! Ваше сообщение отправлено.')
        return render(request, 'contacts.html')
    return render(request, 'contacts.html')
