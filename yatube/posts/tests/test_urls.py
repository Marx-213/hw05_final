from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.text_post = Post.objects.create(
            author=cls.author_user,
            text='Тестовый пост'
        )
        cls.template_url_names = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.author_user}/': 'posts/profile.html',
            f'/posts/{cls.text_post.id}/': 'posts/post_detail.html',
        }
        cls.urls = {
            'create': '/create/',
            'post_edit': f'/posts/{cls.text_post.id}/edit/',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.author_client = Client()
        self.authorized_client.force_login(self.author_user)
        self.author_client.force_login(self.text_post.author)

    def test_posts_available_guest_client(self):
        """Общедоступные страницы доступны любому пользователю"""
        for address, template in self.template_url_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in self.template_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_create_post_edit_available_authorized_user(self):
        """Страницы create и post_edit доступны авторизованным пользователям.
        Запрос к несуществующей странице вернет 404"""
        for name, url in self.urls.items():
            with self.subTest(name=name):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
            response = self.authorized_client.get('/unknown_page/')
            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
