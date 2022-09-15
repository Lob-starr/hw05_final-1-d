from django.contrib import admin

from .models import Comment, Follow, Group, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """
    отображение полей постов в админке:
        pk - ид записи
        text - запись сообщения
        pub_date - дата публикации
        author - автор
        group - группа авторов с возможностью изменять поле.
    """
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """
    отображение полей группы в админке:
        pk - ид записи
        ttile = название группы
        slug = адрес группы
        description = описание группы.
    """
    list_display = (
        'pk',
        'title',
        'slug',
        'description',
    )
    search_fields = ('title',)
    list_filter = ('slug',)
    empty_value_display = '-пусто-'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'created',
        'author',
        'post',
    )
    search_fields = (
        'text',
        'author',
        'post',
    )
    list_filter = ('created',)
    empty_value_display = '-пусто-'


@admin.register(Follow)
class Followadmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'user',
        'author',
    )
    search_fields = ('author',)
    empty_value_display = '-пусто-'
