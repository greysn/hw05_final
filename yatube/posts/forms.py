from django import forms
from django.contrib.auth import get_user_model

from .models import Post, Comment

User = get_user_model()


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        labels = {
            'group': 'Группа',
            'text': 'Текст заметки',
        }
        help_texts = {
            'text': ('Введите текст поста'),
        }
        widgets = {
            'text': forms.Textarea(attrs={'style':
                                          'resize: vertical;'})
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'Текст комментария'}
        help_texts = {'text': 'Hапишите ваш комментарий'}
        widgets = {'text': forms.Textarea({'rows': 3})}
