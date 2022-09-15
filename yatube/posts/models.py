from django.contrib.auth import get_user_model
from django.db import models

from .constants import LIMIT_SYMBOL

User = get_user_model()


class Group(models.Model):
    """
    title - название группы
    slug -  уникальный адрес группы, часть URL
    description - текст, описывающий сообщество.
    """
    title = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(unique=True, verbose_name='Адрес группы')
    description = models.TextField(verbose_name='Описание')

    class Meta:
        verbose_name = ('Группа')
        verbose_name_plural = ('Группы')

    def __str__(self):
        return self.title


class Post(models.Model):
    """
    text - запись сообщения
    pub_date - дата публикации
    author - автор поста
    group - группа поста
    image - картинка к посту.
    """
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Введите текст поста',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор поста',
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа поста',
        help_text='Выберите группу',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = ('Пост')
        verbose_name_plural = ('Посты')

    def __str__(self):
        return self.text[:LIMIT_SYMBOL]


class Comment(models.Model):
    """
    post - пост, к которому относятся комментария
    author - автор сообщения
    text - текст комментария
    created - дата создания.
    """
    post = models.ForeignKey(
        Post,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='comments',
        help_text='Комментарий к посту',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария',
    )
    text = models.TextField(
        'Текст комментария',
        help_text='Введите текст комментария',
    )
    created = models.DateTimeField(
        'Дата комментария',
        auto_now_add=True,
    )

    class Meta:
        ordering = ['-created']
        verbose_name = ('Коммент')
        verbose_name_plural = ('Комменты')

    def __str__(self):
        return self.text[:LIMIT_SYMBOL]


class Follow(models.Model):
    """
    user - подписчик
    author - автор поста
    """
    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = ('Подписка')
        verbose_name_plural = ('Подписки')
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author'
            ),
        )
