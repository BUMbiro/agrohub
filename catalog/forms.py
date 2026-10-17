from django import forms
from PIL import Image

from .models import Product


# ============================================================
# Константы
# ============================================================

# Запрещённые слова: нельзя использовать в названии и описании товара
FORBIDDEN_WORDS = [
    'казино',
    'криптовалюта',
    'крипта',
    'биржа',
    'дешево',
    'бесплатно',
    'обман',
    'полиция',
    'радар',
]

# Разрешённые форматы изображений и максимальный размер (5 МБ)
ALLOWED_IMAGE_FORMATS = ['JPEG', 'PNG']
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 МБ в байтах


# ============================================================
# Форма продукта
# ============================================================

class ProductForm(forms.ModelForm):
    """Форма создания и редактирования товара.

    - Валидирует name и description на запрещённые слова (регистр игнорируется).
    - Проверяет, что цена не отрицательная.
    - Проверяет формат и размер изображения (JPEG/PNG, до 5 МБ).
    - Все поля стилизованы под Bootstrap через __init__.
    """

    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'price', 'unit', 'image', 'in_stock']
        labels = {
            'category': 'Категория',
            'name': 'Наименование',
            'description': 'Описание',
            'price': 'Цена',
            'unit': 'Единица измерения',
            'image': 'Изображение',
            'in_stock': 'В наличии',
        }
        help_texts = {
            'unit': 'Например: шт., кг, л, упак.',
            'image': 'Формат JPEG или PNG, размер до 5 МБ',
        }

    def __init__(self, *args, **kwargs):
        """Стилизация всех полей формы под Bootstrap."""
        super().__init__(*args, **kwargs)

        # Перебираем поля и назначаем Bootstrap-классы
        for field_name, field in self.fields.items():
            widget = field.widget

            # Чекбокс — отдельный класс (Bootstrap форма)
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs['class'] = 'form-check-input'
            # Выпадающие списки
            elif isinstance(widget, forms.Select):
                widget.attrs['class'] = 'form-select'
            # Файлы
            elif isinstance(widget, forms.ClearableFileInput):
                widget.attrs['class'] = 'form-control'
            # Текстовые поля, число, textarea — общий класс
            else:
                widget.attrs['class'] = 'form-control'

            # Placeholder для текстовых полей (если ещё нет)
            if 'placeholder' not in widget.attrs:
                widget.attrs['placeholder'] = field.label

    # --------------------------------------------------------
    # Валидация запрещённых слов
    # --------------------------------------------------------

    @staticmethod
    def _check_forbidden_words(value, field_name):
        """Проверяет текст на запрещённые слова (регистр игнорируется)."""
        if not value:
            return value

        value_lower = value.lower()
        found = [word for word in FORBIDDEN_WORDS if word in value_lower]

        if found:
            words_str = ', '.join(found)
            raise forms.ValidationError(
                f'В поле «{field_name}» нельзя использовать слова: {words_str}.'
            )
        return value

    def clean_name(self):
        """Валидация названия: длина + запрещённые слова."""
        name = self.cleaned_data.get('name', '').strip()

        if len(name) < 2:
            raise forms.ValidationError('Название должно содержать минимум 2 символа.')

        return self._check_forbidden_words(name, 'Наименование')

    def clean_description(self):
        """Валидация описания: запрещённые слова."""
        description = self.cleaned_data.get('description', '')
        return self._check_forbidden_words(description, 'Описание')

    # --------------------------------------------------------
    # Валидация цены
    # --------------------------------------------------------

    def clean_price(self):
        """Цена не может быть отрицательной."""
        price = self.cleaned_data.get('price')

        if price is None:
            return price

        if price < 0:
            raise forms.ValidationError('Цена не может быть отрицательной.')

        return price

    # --------------------------------------------------------
    # Валидация изображения (доп. задание)
    # --------------------------------------------------------

    def clean_image(self):
        """Изображение: только JPEG или PNG, размер не более 5 МБ."""
        image = self.cleaned_data.get('image')

        # Если поле пустое (при редактировании можно не менять) — пропускаем
        if not image:
            return image

        # Если это уже существующий файл из БД (не новая загрузка) — пропускаем
        if not hasattr(image, 'content_type'):
            return image

        # Проверка размера
        if image.size > MAX_IMAGE_SIZE:
            raise forms.ValidationError(
                f'Размер изображения не должен превышать 5 МБ. '
                f'Ваш файл: {image.size / (1024 * 1024):.1f} МБ.'
            )

        # Проверка формата через Pillow
        try:
            img = Image.open(image)
            img_format = img.format
        except Exception:
            raise forms.ValidationError('Не удалось прочитать изображение. Загрузите корректный файл.')

        if img_format not in ALLOWED_IMAGE_FORMATS:
            raise forms.ValidationError(
                f'Недопустимый формат изображения: {img_format}. '
                f'Разрешены только: {", ".join(ALLOWED_IMAGE_FORMATS)}.'
            )

        # Возвращаем указатель в начало файла, иначе Django сохранит пустой файл
        image.seek(0)
        return image
