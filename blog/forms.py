from django import forms
from .models import BlogPost


class BlogPostForm(forms.ModelForm):
    """Форма для создания и редактирования статьи блога."""

    class Meta:
        model = BlogPost
        fields = ['title', 'content', 'preview', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Заголовок статьи',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Содержимое статьи',
            }),
            'preview': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'title': 'Заголовок',
            'content': 'Содержимое',
            'preview': 'Превью',
            'is_published': 'Опубликовать',
        }

    def clean_title(self):
        """Заголовок не короче 3 символов."""
        title = self.cleaned_data.get('title')
        if title and len(title.strip()) < 3:
            raise forms.ValidationError('Заголовок слишком короткий')
        return title.strip()
