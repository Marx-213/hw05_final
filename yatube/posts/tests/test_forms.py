import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username='NoName1')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.form = PostForm()
        cls.text_post = Post.objects.create(
            author=cls.author_user,
            text='Тестовый пост',
        )
        cls.form_data = {
            'text': f'{cls.text_post.text}',
            'group': f'{cls.group.id}',
        }
        cls.comment = Comment.objects.create(
            author=cls.author_user,
            text='Тестовый коммент',
        )
        cls.comment_form_data = {
            'text': f'{cls.comment.text}',
        }

    def setUp(cls):
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.author_client = Client()
        cls.authorized_client.force_login(cls.author_user)
        cls.author_client.force_login(cls.text_post.author)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_form_with_image(self):
        """Форма с картинкой создает запись в Post."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': f'{self.text_post.text}',
            'group': f'{self.group.id}',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, f'/profile/{self.author_user}/')
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                author=self.author_user,
                text=self.text_post.text,
                group=self.group.id,
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        """Проверка редактирования поста."""
        posts_count = Post.objects.count()
        response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.text_post.id}),
            data=self.form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(
            Post.objects.filter(
                text=self.text_post.text,
                author=self.author_user,
                group=self.group.id
            ).exists()
        )

    def test_create_comment(self):
        """Проверка создания комментария."""
        comment_count = Comment.objects.count()
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': f'{self.text_post.id}'}),
            data=self.comment_form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': f'{self.text_post.id}'}))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=self.comment.text,
                author=self.author_user,
            ).exists()
        )

    def test_comment_in_post_detail(self):
        """Комментарий появляется на странице поста."""
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': f'{self.text_post.id}'}),
            data=self.comment_form_data,
            follow=True
        )
        self.assertEqual(
            response.context['comments'][0].text,
            self.comment.text
        )
