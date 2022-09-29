import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Group, Post, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='ilya')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTest.user)

    def test_create_post(self):
        """Валидная форма создает пост в БД."""
        post_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=PostFormTest.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': PostFormTest.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        created_post = Post.objects.latest('pk')
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(created_post.group.id, form_data['group'])
        self.assertEqual(created_post.author, PostFormTest.user)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': created_post.author})
        )
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                image='posts/small.gif'
            ).exists()
        )

    def test_post_edit_form(self):
        """Валидная форма редактирует пост
        а так же юзер может оставить коммент под постом."""
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            group=PostFormTest.group,
            author=PostFormTest.user,
            text='Тестовый пост'
        )
        group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание 2'
        )
        comment = Comment.objects.create(
            text='Коммент',
            author=PostFormTest.user,
            post=post
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста',
            'group': group_2.id,
            'comments': comment
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': post.pk})
        )
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                id=post.pk,
                group=form_data['group'],
                comments=form_data['comments']
            ).exists()
        )
        self.client.get(
            (reverse
                ('posts:group_list', kwargs={'slug': PostFormTest.group.slug}))
        )
        zero_posts_on_page = 0
        self.assertEqual(
            Post.objects.filter(group=PostFormTest.group).count(),
            zero_posts_on_page
        )

    def test_anonymous_dont_create_post(self):
        """Анонимный пользователь не может создать пост"""
        form_data = {
            'text': 'Текст от анонима',
            'group': PostFormTest.group.id
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text'],
            ).exists()
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_anonymous_dont_create_comment(self):
        """Аноним не может оставить коммент под постом"""
        post = Post.objects.create(
            group=self.group,
            author=self.user,
            text='Text'
        )
        response = self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.pk})
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{post.pk}/comment/'
        )
