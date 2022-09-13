from django.test import TestCase

from ..constants import LIMIT_SYMBOL
from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост больше 15 символов',
        )

    def test_models_have_correct_object_names(self):
        """Проверка __str__."""
        self.assertEqual(str(self.post), self.post.text[:LIMIT_SYMBOL])
        self.assertEqual(str(self.group), self.group.title)

    def test_post_model_verbose_name(self):
        """Проверка verbose_name."""
        expected_value_verbose = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор поста',
            'group': 'Группа поста',
        }
        for field, expected_value in expected_value_verbose.items():
            with self.subTest(field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value,
                )

    def test_title_help_text(self):
        """Проверка help_text."""
        expected_value_help = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
        }
        for field, expected_value in expected_value_help.items():
            with self.subTest(field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text,
                    expected_value
                )
