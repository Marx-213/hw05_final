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
        cls.post = Post.objects.create(
            author=cls.author_user,
            text='Тестовый пост'
        )
        cls.template_url_names = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.author_user}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
        }
        cls.urls = {
            'create': '/create/',
            'post_edit': f'/posts/{cls.post.id}/edit/',
            'unknown_page': '/unknown_page/',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.author_client = Client()
        self.authorized_client.force_login(self.author_user)
        self.author_client.force_login(self.post.author)

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

    def test_posts_create_url_available_authorized_user(self):
        for name, url in self.urls.items():
            with self.subTest(name=name):
                if name == 'create':
                    response = self.authorized_client.get('/create/')
                    self.assertEqual(response.status_code, HTTPStatus.OK)
                    self.assertTemplateUsed(response, 'posts/create_post.html')
                    response = self.guest_client.get('/create/', follow=True)
                    self.assertRedirects(
                        response, '/auth/login/?next=/create/'
                    )
                elif name == 'post_edit':
                    response = self.author_client.get(
                        f'/posts/{self.post.id}/edit/'
                    )
                    self.assertEqual(response.status_code, HTTPStatus.OK)
                    response = self.guest_client.get(
                        f'/posts/{self.post.id}/edit/', follow=True
                    )
                    self.assertRedirects(
                        response,
                        f'/auth/login/?next=/posts/{self.post.id}/edit/'
                    )
                else:
                    response = self.guest_client.get('/unknown_page/')
                    self.assertEqual(
                        response.status_code, HTTPStatus.NOT_FOUND
                    )
