from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст поста',
            'group': 'Группа поста',
            'image': 'Изображение'
        }
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Загрузите картинку'
        }

    def clean_text(self):
        text = self.cleaned_data['text']
        if text == '':
            raise forms.ValidationErrors('В поле text пусто!')
        return text


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': 'Текст комментария'}
        help_text = {'text': 'Напишите коммент'}
