import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from mixer.backend.django import mixer

from ..constants import (COUNT_POST_FOR_TEST, LIMIT_POST, LIMIT_POST_FOR_TEST,
                         ZERO_FOR_FOLLOW_INDEX)
from ..models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user_test')
        cls.user_for_follow = User.objects.create_user(username='Test follow')
        cls.group = Group.objects.create(
            title='тестовая группа',
            slug='test',
            description='тестовое описание',
        )
        cls.new_group = Group.objects.create(
            title='тестовая группа 2',
            slug='test2',
            description='тестовое описание 2',
        )
        cls.posts = mixer.cycle(COUNT_POST_FOR_TEST).blend(
            Post,
            author=cls.user,
            group=cls.group,
            text=mixer.RANDOM,
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
            content_type='image/gif',
        )
        cls.post_with_image = Post.objects.create(
            author=cls.user,
            text='Пост с картинкой',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.posts_test = Post.objects.filter(
            group_id=cls.group.id
        )[:LIMIT_POST]
        cls.templates_pages_names = {
            reverse('posts:index'):
                'posts/index.html',
            reverse('posts:group_posts', kwargs={'slug': cls.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': cls.posts_test[0].author}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': cls.posts_test[0].id}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': cls.posts_test[0].id}):
                'posts/create_post.html',
            reverse('posts:post_create'):
                'posts/create_post.html',
        }
        cls.urls_with_paginator = {
            reverse('posts:index'),
            reverse(
                'posts:group_posts', kwargs={'slug': cls.group.slug},
            ),
            reverse(
                'posts:profile', kwargs={'username': cls.posts_test[0].author},
            ),
        }
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Создание пользователей."""
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.auth_client_follow = Client()
        self.auth_client_follow.force_login(self.user_for_follow)

    def context_for_test(self, response, temp):
        objects = list(response.context[temp])
        self.assertEqual(objects[0], self.posts_test[0])
        self.assertEqual(objects[0].author, self.posts_test[0].author)
        self.assertEqual(objects[0].group, self.posts_test[0].group)
        self.assertEqual(objects[0].text, self.posts_test[0].text)
        self.assertEqual(objects[0].image, self.posts_test[0].image)

    def test_correct_templates(self):
        """Проверка на соответствии шаблона с адресом."""
        for reverse_url, template in self.templates_pages_names.items():
            with self.subTest(template):
                response = self.authorized_client.get(reverse_url)
                self.assertTemplateUsed(response, template)

    def test_paginator(self):
        """
        Проверка на наличии 10 постов на первой странице и
        4 постов на след.странице.
        """
        for reverse_url in self.urls_with_paginator:
            with self.subTest(reverse_url):
                response = self.authorized_client.get(reverse_url)
                self.assertEqual(
                    len(response.context['page_obj']), LIMIT_POST
                )
                response_next_page = self.authorized_client.get(
                    reverse_url + '?page=2'
                )
                self.assertEqual(
                    len(response_next_page.context['page_obj']),
                    LIMIT_POST_FOR_TEST
                )

    def test_context_index(self):
        """Проверка контекстов страницы index."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.context_for_test(response, 'page_obj')

    def test_context_group_list(self):
        """Проверка контекстов страницы group_list."""
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug})
        )
        self.context_for_test(response, 'page_obj')
        self.assertEqual(response.context['group'], self.group)

    def test_context_profile(self):
        """Проверка контекстов страницы profile."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.posts_test[0].author})
        )
        self.context_for_test(response, 'page_obj')
        self.assertEqual(response.context['author'], self.user)

    def test_context_post_detail(self):
        """Проверка контекстков страницы post_detail."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.posts_test[0].id})
        )
        object = response.context['post']
        self.assertEqual(object.id, self.posts_test[0].id)
        self.assertEqual(object.author, self.posts_test[0].author)
        self.assertEqual(object.group, self.posts_test[0].group)
        self.assertEqual(object.text, self.posts_test[0].text)
        self.assertEqual(object.image, self.posts_test[0].image)

    def test_new_post_in_need_pages(self):
        """Проверка новый пост попал на нужные страницы и на первой позиции."""
        new_post = Post.objects.create(
            author=self.user,
            group=self.group,
            text='Новое сообщение'
        )
        pages = [
            reverse(
                'posts:index'
            ),
            reverse(
                'posts:group_posts', kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile', kwargs={'username': self.posts_test[0].author}
            ),
        ]
        for url in pages:
            with self.subTest(url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    new_post,
                    response.context['page_obj'][0]
                )

    def test_new_post_in_need_group(self):
        """Проверка новый пост находится в нужной группе."""
        new_post = Post.objects.create(
            author=self.user,
            group=self.new_group,
            text='Новое сообщение'
        )
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.new_group.slug})
        )
        objects = response.context['page_obj']
        self.assertNotEqual(objects[0].group, self.group)
        self.assertNotIn(new_post, self.posts_test)

    def test_context_post_create(self):
        """Проверка контекста страницы post_create."""
        reverse_url = reverse('posts:post_create')
        response = self.authorized_client.get(reverse_url)
        for value, expected in self.form_fields.items():
            with self.subTest(value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_context_post_edit(self):
        """Проверка контекста страницы post_edit."""
        reverse_url = reverse(
            'posts:post_edit', kwargs={'post_id': self.posts_test[0].id}
        )
        response = self.authorized_client.get(reverse_url)
        for value, expected in self.form_fields.items():
            with self.subTest(value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertEqual(
            response.context['post_id'],
            self.posts_test[0].id
        )
        self.assertEqual(response.context['is_edit'], True)

    def test_cache(self):
        """Проверка кэша страницы Index."""
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        Post.objects.create(
            text='Проверяем кэширование страницы',
            author=self.user,
        )
        cached = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertEqual(
            response.content,
            cached.content
        )
        cache.clear()
        response_new = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertNotEqual(cached.content, response_new.content)

    def test_follow(self):
        """Проверка подписки."""
        response = self.auth_client_follow.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), ZERO_FOR_FOLLOW_INDEX)
        self.auth_client_follow.get(
            reverse('posts:profile_follow', kwargs={'username': self.user})
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_for_follow,
                author=self.user
            ).exists()
        )

    def test_unfollow(self):
        """Проверка отписки."""
        Follow.objects.create(
            user=self.user_for_follow,
            author=self.user
        )
        self.auth_client_follow.get(
            reverse('posts:profile_unfollow', kwargs={'username': self.user})
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_for_follow,
                author=self.user
            ).exists()
        )

    def test_show_post_followed(self):
        """Проверка отображения постов у подписанных."""
        Follow.objects.create(
            user=self.user_for_follow,
            author=self.user
        )
        response = self.auth_client_follow.get(
            reverse('posts:follow_index')
        )
        objects = list(response.context['page_obj'])
        self.assertIn(objects[0], self.posts_test)

    def test_no_show_post_unfollowed(self):
        """Проверка неотображения постов у неподписанных."""
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        objects = list(response.context['page_obj'])
        self.assertNotIn(objects, self.posts_test)
