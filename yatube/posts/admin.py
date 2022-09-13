from django.contrib import admin

from .models import Group, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """
    отображение полей в админке:
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


admin.site.register(Group)
