import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.conf import settings
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Group, Post, User, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='ilya')
        cls.follower_user = User.objects.create_user(username='fiji')
        cls.not_follower = User.objects.create_user(username='not_follow')
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
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.user,
            text='Тестовый пост'
        )
        cls.index_page = reverse('posts:index')
        cls.group_list_page = reverse(
            'posts:group_list', kwargs={'slug': 'test-slug'}
        )
        cls.profile_page = reverse(
            'posts:profile', kwargs={'username': cls.user}
        )
        cls.post_detail_page = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.pk}
        )
        cls.post_create_page = reverse('posts:post_create')
        cls.post_edit_page = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.pk}
        )
        cls.urls_list = [
            (cls.index_page, 'posts/index.html'),
            (cls.group_list_page, 'posts/group_list.html'),
            (cls.profile_page, 'posts/profile.html'),
            (cls.post_detail_page, 'posts/post_detail.html'),
            (cls.post_create_page, 'posts/create_post.html'),
            (cls.post_edit_page, 'posts/create_post.html')
        ]
        cls.pages_with_paginator = [
            (cls.index_page),
            (cls.group_list_page),
            (cls.profile_page)
        ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)
        self.follower_client = Client()
        self.follower_client.force_login(PostPagesTests.follower_user)
        self.not_follower_client = Client()
        self.not_follower_client.force_login(PostPagesTests.not_follower)
        cache.clear()

    def asserts(self, first_obj):
        self.assertEqual(first_obj.author, PostPagesTests.user)
        self.assertEqual(first_obj.group, PostPagesTests.group)
        self.assertEqual(first_obj.pk, PostPagesTests.post.pk)
        self.assertEqual(first_obj.image, PostPagesTests.post.image)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in PostPagesTests.urls_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(PostPagesTests.index_page)
        first_obj = response.context['page_obj'][0]
        self.asserts(first_obj)
        self.assertEqual(response.context['title'], 'YaTube')
        self.assertEqual(response.context['is_edit'], True)
        self.assertEqual(response.context['all_posts_author'], True)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(PostPagesTests.profile_page)
        first_obj = response.context['page_obj'][0]
        self.asserts(first_obj)
        self.assertEqual(response.context['is_edit'], True)
        self.assertEqual(
            response.context['title'],
            f'Профайл пользователя {PostPagesTests.user.username}'
        )
        self.assertEqual(
            response.context['post_count'], PostPagesTests.post.pk
        )

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(PostPagesTests.group_list_page)
        first_obj = response.context['page_obj'][0]
        self.asserts(first_obj)
        self.assertEqual(response.context['all_posts_author'], True)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(PostPagesTests.post_detail_page)
        self.assertEqual(
            response.context['post'].id, PostPagesTests.post.pk
        )
        self.assertEqual(
            response.context['post'].image, PostPagesTests.post.image
        )
        self.assertEqual(
            response.context['post'].comments, PostPagesTests.post.comments
        )
        self.assertEqual(
            response.context['title'], f'Пост {PostPagesTests.post}'
        )
        self.assertEqual(
            response.context['author_post'], PostPagesTests.post.author
        )
        self.assertEqual(response.context['post'], PostPagesTests.post)
        self.assertEqual(
            response.context['post_count'], PostPagesTests.post.pk
        )

    def test_post_edit_page_show_correct_context(self):
        """
        Шаблон create_post для post_edt сформирован с правильным контекстом.
        """
        response = self.authorized_client.get(PostPagesTests.post_edit_page)
        form_fields = [
            ('text', forms.fields.CharField),
            ('group', forms.fields.ChoiceField),
        ]
        for value, expected in form_fields:
            with self.subTest(value=value):
                form_field = response.context['form'].fields.get(value)
                self.assertEqual(response.context['is_edit'], True)
                self.assertIsInstance(form_field, expected)

    def test_post_create_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(PostPagesTests.post_create_page)
        form_fields = [
            ('text', forms.fields.CharField),
            ('group', forms.fields.ChoiceField),
        ]
        for value, expected in form_fields:
            with self.subTest(value=value):
                form_field = response.context['form'].fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_included_in_another_group(self):
        """Проверка на то, что пост не попал в группу, для которой
        он не предназначен.
        """
        self.group_2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2',
        )
        self.post_2 = Post.objects.create(
            group=self.group_2,
            author=PostPagesTests.user,
            text='Тестовый пост2'
        )
        response = self.authorized_client.get(PostPagesTests.group_list_page)
        response_2 = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug2'})
        )
        self.assertEqual(
            response.context['post'].group, PostPagesTests.post.group
        )
        self.assertEqual(response_2.context['post'].group, self.post_2.group)

    def test_first_page_contains_ten_records(self):
        """Проверка количества постов на страницах."""
        self.posts = [(Post(
            author=PostPagesTests.user,
            text=f'Тестовый пост {i}',
            group=PostPagesTests.group))
            for i in range(13)
        ]
        Post.objects.bulk_create(self.posts)
        page_postfixurl_posts = [(1, 10), (2, 4)]
        for page_pag, posts in page_postfixurl_posts:
            for page in PostPagesTests.pages_with_paginator:
                with self.subTest(page=page):
                    response = self.client.get(page, {'page': page_pag})
                    self.assertEqual(len(response.context['page_obj']), posts)

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        first_response = self.authorized_client.get(PostPagesTests.index_page)
        post = Post.objects.get(pk=1)
        post.text = 'Измененный текст'
        post.save()
        second_response = self.authorized_client.get(PostPagesTests.index_page)
        self.assertEqual(first_response.content, second_response.content)
        cache.clear()
        third_response = self.authorized_client.get(PostPagesTests.index_page)
        self.assertNotEqual(first_response.content, third_response.content)

    def test_authorized_user_can_follow(self):
        """Авторизованный пользователь может подписаться на автора
        и отписаться."""
        self.follower_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': PostPagesTests.user.username})
        )
        follow_count = Follow.objects.all().count()
        self.assertEqual(follow_count, 1)
        self.follower_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': PostPagesTests.user.username})
        )
        unfollow_count = Follow.objects.all().count()
        self.assertEqual(unfollow_count, 0)

    def test_new_post_appears_in_the_subscribers(self):
        """Новый пост появляется у подписчиков автора поста
        и отсутвует у тех кто не подписан на автора."""
        self.new_post = Post.objects.create(
            group=PostPagesTests.group,
            author=PostPagesTests.user,
            text='Написал новый пост'
        )
        Follow.objects.create(
            user=PostPagesTests.follower_user,
            author=PostPagesTests.user
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual(
            response.context['page_obj'][0].text, self.new_post.text
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotContains(
            response, self.new_post.text
        )
