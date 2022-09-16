import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user_test')
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовое сообщение',
            group=cls.group,
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.new_uploaded = SimpleUploadedFile(
            name='new_small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.posts_count = Post.objects.count()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        """Проверка на создание записи и валидность формы."""
        reverse_url = reverse('posts:post_create')
        posts_before_posting = list(Post.objects.values_list('id', flat=True))
        form_data = {
            'text': 'Новое тестовое сообщение',
            'group': self.group.id,
            'author': self.user,
            'image': self.new_uploaded,
        }
        response = self.authorized_client.post(
            reverse_url,
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), self.posts_count + 1)
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={"username": self.user.username})
        )
        post_upd = Post.objects.exclude(id__in=posts_before_posting)
        self.assertTrue(post_upd)
        self.assertEqual(len(post_upd), 1)
        self.assertEqual(post_upd[0].text, form_data['text'])
        self.assertEqual(post_upd[0].group.id, form_data['group'])
        self.assertEqual(post_upd[0].author, form_data['author'])
        self.assertEqual(post_upd[0].image, 'posts/new_small.gif')

    def test_post_edit(self):
        """Проверка формы изменения записи и валидность."""
        reverse_url = reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}
        )
        uploaded = SimpleUploadedFile(
            name='new_big.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Измененное сообщение',
            'group': self.new_group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse_url,
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), self.posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=self.user,
                group=self.new_group,
                id=self.post.id,
                image='posts/new_big.gif'
            ).exists()
        )

    def test_guest_cant_edit_post(self):
        """Проверка на создание поста гостем."""
        reverse_url = reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}
        )
        form_data = {
            'text': 'Измененное сообщение',
            'group': self.group.id
        }
        response = self.client.post(
            reverse_url,
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), self.posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )

    def test_add_comment(self):
        """Проверка создания комментарий."""
        comment_count = Comment.objects.count()
        comments_before_posting = list(
            Comment.objects.values_list('id', flat=True)
        )
        form_data = {
            'text': 'Тестовый комментарий'
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        comment_upd = Comment.objects.exclude(id__in=comments_before_posting)
        self.assertTrue(comment_upd)
        self.assertEqual(comment_upd[0].text, form_data['text'])
        self.assertEqual(comment_upd[0].author, self.user)
        self.assertEqual(
            Comment.objects.count(),
            comment_count + 1
        )
        self.assertRedirects(
            response, reverse(
                "posts:post_detail",
                kwargs={"post_id": self.post.id}
            )
        )

    def test_guest_cant_add_comment(self):
        """Проверка создания комментарий гостем."""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий'
        }
        response = self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(
            Comment.objects.count(),
            comment_count
        )
        self.assertFalse(
            Comment.objects.filter(
                text=form_data['text'],
            ).exists()
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/comment/'
        )
