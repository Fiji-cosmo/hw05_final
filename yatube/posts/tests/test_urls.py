from django.test import TestCase, Client

from http import HTTPStatus

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='ilya')
        cls.not_author = User.objects.create_user(username='fiji')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='hello world',
        )
        cls.public_urls = [
            ('/', 'posts/index.html'),
            (f'/group/{cls.group.slug}/', 'posts/group_list.html'),
            (f'/profile/{cls.user.username}/', 'posts/profile.html'),
            (f'/posts/{cls.post.pk}/', 'posts/post_detail.html'),
        ]
        cls.post_edit_url = f'/posts/{cls.post.pk}/edit/'
        cls.create_url = '/create/'
        cls.private_urls = [
            (cls.create_url, 'posts/create_post.html'),
            (cls.post_edit_url, 'posts/create_post.html')
        ]
        cls.redirect_urls_for_anon = [
            (cls.create_url, f'/auth/login/?next={cls.create_url}'),
            (cls.post_edit_url, f'/auth/login/?next={cls.post_edit_url}')
        ]

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)
        self.not_author_client = Client()
        self.not_author_client.force_login(PostURLTests.not_author)

    def test_posts_urls_exists_at_desired_location(self):
        """Общедоступные страницы доступны любому пользователю и используют
        соответствующий шаблон."""
        for address, template in PostURLTests.public_urls:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_post_create_and_edit_exists_at_desired_location_authorized(self):
        """Страницы доступны для авторизованных пользователей и используют
        соответствующий шаблон."""
        for adress, template in PostURLTests.private_urls:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_post_edit_not_available_to_not_author(self):
        """Страница /posts/<post_id>/edit/ перенаправит пользователя сайта
        но не афтора на страницу с информацией поста.
        """
        response = self.not_author_client.get(
            PostURLTests.post_edit_url, follow=True
        )
        self.assertRedirects(response, f'/posts/{PostURLTests.post.pk}/')

    def test_urls_redirect_anonymous_on_login(self):
        """Страницы перенаправят анонимного пользователя на страницу логина."""
        for url, redirect in PostURLTests.redirect_urls_for_anon:
            with self.subTest(url=url):
                response = self.client.get(url, follow=True)
                self.assertRedirects(response, redirect)

    def test_error_page(self):
        """Несуществующая страница вернет код 404"""
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
