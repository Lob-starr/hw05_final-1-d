from http import HTTPStatus

from django.test import Client, TestCase

from ..models import Group, Post, User


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user_test')
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug='test',
            description='тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост больше 15 символов',
            group=cls.group,
        )
        cls.templates_url = {
            '/',
            f'/group/{cls.group.slug}/',
            f'/profile/{cls.user.username}/',
            f'/posts/{cls.post.id}/',
        }
        cls.all_templates_urls = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        cls.urls_for_author = {
            '/create/': 'posts/create_post.html',
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
        }

    def setUp(self):
        """Создание пользователей."""
        self.user = User.objects.create_user(username='No author')
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(self.user)
        self.author = User.objects.get(username='user_test')
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)

    def test_urls_for_all(self):
        """Проверка соответствии адреса с шаблоном."""
        for adress, template in self.all_templates_urls.items():
            with self.subTest(template):
                response = self.authorized_client_author.get(adress)
                self.assertTemplateUsed(response, template)

    def test_urls_for_author(self):
        """Проверка всех адресов автором поста."""
        for adress, template in self.all_templates_urls.items():
            with self.subTest(adress):
                response = self.authorized_client_author.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_for_auth_author(self):
        """
        Проверка доступности страницы создания и редактирования поста,
        только автору поста.
        """
        for adress in self.urls_for_author:
            response = self.authorized_client_author.get(adress)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_for_guest(self):
        """Проверка страницы post_edit гостем."""
        response = self.client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )

    def test_post_edit_for_not_author(self):
        """Проверка страницы post_edit не автором."""
        response = self.authorized_client_not_author.get(
            f'/posts/{self.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response, f'/posts/{self.post.id}/'
        )

    def test_urls_for_auth(self):
        """Проверка доступности страницы гостем и редирект на логин."""
        response = self.client.get('/create/')
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_404_page(self):
        """Проверка страницы 404."""
        response = self.client.get('/unknow_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
