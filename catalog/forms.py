from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    """Форма добавления нового товара. Все поля обязательны, кроме image и in_stock."""

    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'price', 'unit', 'image', 'in_stock']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Томат Черри'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Краткое описание товара'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'шт., кг, л, упак.'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'in_stock': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'category': 'Категория',
            'name': 'Наименование',
            'description': 'Описание',
            'price': 'Цена',
            'unit': 'Единица измерения',
            'image': 'Изображение',
            'in_stock': 'В наличии',
        }
        error_messages = {
            'name': {'required': 'Укажите название товара'},
            'description': {'required': 'Добавьте описание'},
            'price': {'required': 'Укажите цену'},
            'category': {'required': 'Выберите категорию'},
        }

    def clean_price(self):
        """Дополнительная проверка: цена должна быть положительной."""
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise forms.ValidationError('Цена должна быть больше нуля')
        return price

    def clean_name(self):
        """Имя не должно быть короче 2 символов."""
        name = self.cleaned_data.get('name')
        if name and len(name.strip()) < 2:
            raise forms.ValidationError('Название слишком короткое')
        return name.strip()
