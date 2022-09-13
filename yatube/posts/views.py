from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .constants import CACHE_TIME
from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import paginator_post


@cache_page(CACHE_TIME)
def index(request):
    """
    Передаёт в шаблон index.html десять последних объектов модели.
    """
    template = 'posts/index.html'
    posts = Post.objects.select_related('group', 'author')
    page_obj = paginator_post(request, posts)
    context = {
        'page_obj': page_obj,
    }

    return render(request, template, context)


def group_posts(request, slug):
    """
    Передаёт в шаблон group_list.html десять последних объектов модели.
    """
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginator_post(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }

    return render(request, template, context)


def profile(request, username):
    """
    Передача данных в шаблон profile.html.
    """
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post = author.posts.all()
    page_obj = paginator_post(request, post)
    following = author.following.exists()
    context = {
        'author': author,
        'page_obj': page_obj,
        'post': post,
        'following': following,
    }

    return render(request, template, context)


def post_detail(request, post_id):
    """
    Передача данных в шаблон post_detail.html.
    """
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }

    return render(request, template, context)


@login_required
def post_create(request):
    """
    Передача формы создания сообщения в шаблон create_post.html.
    """
    template = 'posts/create_post.html'
    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES or None,
        )

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', post.author)

        return render(request, template, {'form': form})
    form = PostForm()

    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    """
    Передача формы редактирования сообщения в шаблон create_post.html.
    """
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)

    return render(
        request,
        template,
        {'form': form,
         'is_edit': True,
         'post_id': post.id,
         },
    )


@login_required
def add_comment(request, post_id):
    """Передача формы комментарии."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Передача данных в follow.html."""
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator_post(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Передача инфы о подписке."""
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    """Передача инфы о отписке."""
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get(user=request.user, author=author).delete()
    return redirect('posts:follow_index')
