from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост и пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        post = self.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_object_name_is_title_fild(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        group = self.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        group = self.group
        field_verboses = {
            'title': 'заголовок',
            'slug': 'слаг',
            'description': 'описание',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = self.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)
