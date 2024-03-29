from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username='NoName1')
        cls.followed_user = User.objects.create_user(username='NoName2')
        cls.not_followed_user = User.objects.create_user(username='NoName3')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.image_post = Post.objects.create(
            author=cls.author_user,
            text='Тестовый пост',
            image='posts/image.png'
        )
        cls.cache_post = Post.objects.create(
            author=cls.author_user,
            text='Тестовый пост'
        )
        cls.follows = Follow.objects.create(
            user=cls.followed_user,
            author=cls.image_post.author
        )
        cls.form_data = {
            'text': f'{cls.image_post.text}',
            'group': f'{cls.group.id}',
        }
        cls.comment = Comment.objects.create(
            post=cls.image_post,
            author=cls.author_user,
            text='Тестовый коммент',
        )
        cls.comment_form_data = {
            'text': f'{cls.comment.text}',
        }
        cls.templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{cls.group.slug}'}): (
                'posts/group_list.html'
            ),
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{cls.image_post.id}'}): (
                'posts/post_detail.html'
            ),
            reverse(
                'posts:profile',
                kwargs={'username': f'{cls.image_post.author}'}):
                    'posts/profile.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }
        cls.correct_context_names = {
            'index': reverse('posts:index'),
            'post_detail': reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{cls.image_post.id}'}),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': f'{cls.image_post.author}'})
        }

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.followed_client = Client()
        self.not_followed_client = Client()
        self.author_client.force_login(self.image_post.author)
        self.followed_client.force_login(self.followed_user)
        self.not_followed_client.force_login(self.not_followed_user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(template=template):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

        response = self.author_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': f'{self.image_post.id}'}))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_create_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.author_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': f'{self.image_post.id}'}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.author_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': f'{self.group.slug}'})
        )
        group = response.context['group']
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.description, self.group.description)

    def test_views_show_correct_context(self):
        """Шаблоны index, post_detail, profile с правильным контекстом."""
        for name, reverse_name in self.correct_context_names.items():
            with self.subTest(name=name):
                response = self.author_client.get(reverse_name)
                self.assertEqual(
                    response.context['post'].author,
                    self.image_post.author
                )
                self.assertEqual(
                    response.context['post'].text, self.image_post.text)

    def test_cache(self):
        """Проверка кеширования на странице index """
        response = self.client.get(reverse('posts:index'))
        self.assertContains(response, self.cache_post.text)
        self.assertContains(response, self.cache_post.author)
        self.cache_post.delete()
        cache.clear()
        self.assertContains(response, self.cache_post.text)
        self.assertContains(response, self.cache_post.author)

    def test_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей.
        """
        follows_count = Follow.objects.count()
        response = self.author_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': f'{self.followed_user}'}),
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': f'{self.followed_user}'})
        )
        self.assertEqual(Follow.objects.count(), follows_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.author_user,
                author=self.followed_user
            ).exists()
        )

    def test_unfollow(self):
        """Авторизованный пользователь может удалять
        пользователей из подписок .
        """
        follows_count = Follow.objects.count()
        response = self.followed_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': f'{self.author_user}'}),
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': f'{self.author_user}'})
        )
        self.assertEqual(Follow.objects.count(), follows_count - 1)
        self.assertFalse(
            Follow.objects.filter(
                user=self.author_user,
                author=self.followed_user
            )
        )

    def test_follow_index_show_correct_context(self):
        '''Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан.
        '''
        response = self.followed_client.get(reverse('posts:follow_index'))
        self.assertEqual(
            response.context['page_obj'][0].text,
            self.image_post.text
        )
        self.assertEqual(
            response.context['page_obj'][0].author, self.image_post.author
        )
        self.assertEqual(
            response.context['page_obj'][0].text, self.image_post.text
        )
        response = self.not_followed_client.get(reverse('posts:follow_index'))
        self.assertNotContains(response, self.image_post.text)
        self.assertNotContains(response, self.image_post.author)

    def test_comments_guest_redirect(self):
        """Гость не может комментировать посты
        и перенаправляется на страницу логина."""
        comment_count = Comment.objects.count()
        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': f'{self.image_post.id}'}),
            data=self.comment_form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.image_post.id}/comment/'
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertTrue(
            Comment.objects.filter(
                text=self.comment.text,
                author=self.author_user,
            ).exists()
        )

    def test_guest_can_not_edit_post(self):
        """Гость не может редактировать посты
        и перенаправляется на страницу логина"""
        response = self.guest_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.image_post.id}'}
            ),
            data=self.form_data,
            follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.image_post.id}/edit/'
        )

    def test_users_can_not_edit_post(self):
        """Пользователи не могут изменять чужие посты."""
        response = self.followed_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.image_post.id}'}
            ),
            data=self.form_data,
            follow=True
        )
        self.assertRedirects(
            response, f'/profile/{self.author_user}/'
        )

    def test_guest_can_not_create_post(self):
        """Гость не может создавать посты
        и перенаправляется на страницу логина"""
        posts_count = Post.objects.count()
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': f'{self.author_user}'})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=self.image_post.text,
                author=self.author_user,
                group=self.group.id
            ).exists()
        )

    def test_comment_in_post_detail(self):
        """Комментарий появляется на странице поста."""
        response = self.author_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': f'{self.image_post.id}'}),
            data=self.comment_form_data,
            follow=True
        )
        self.assertEqual(
            response.context['comments'][0].text,
            self.comment.text
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName1')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.posts_count = 13
        cls.posts = Post.objects.bulk_create([Post(
            id=id,
            author=cls.user,
            text=f'Тестовый пост {id}',
            group=cls.group) for id in range(cls.posts_count)
        ])
        cls.paginator_context_names = {
            'index': '/',
            'group_list': f'/group/{cls.group.slug}/',
            'profile': f'/profile/{cls.user}/'
        }

    def test_paginator_correct_context(self):
        """index, group_list, profile содержат 10 постов на первой странице"""
        for name, url in self.paginator_context_names.items():
            with self.subTest(name=name):
                response = self.client.get(url)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_paginator_correct_context_2(self):
        """index, group_list, profile содержат 3 поста на второй странице"""
        for name, url in self.paginator_context_names.items():
            with self.subTest(name=name):
                response = self.client.get(url + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)
