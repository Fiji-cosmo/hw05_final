from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Post, Group, User
from .utils import get_page_context

TEXT_SLICE = 30


@cache_page(20 * 15)
def index(request):
    template = 'posts/index.html'
    page_obj = get_page_context(
        Post.objects.select_related('author', 'group'), request
    )
    is_edit = True
    all_posts_author = True
    context = {
        'title': 'YaTube',
        'text': 'Последние обновления на сайте',
        'page_obj': page_obj,
        'is_edit': is_edit,
        'all_posts_author': all_posts_author,
    }
    return render(request, template, context, )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    template = 'posts/group_list.html'
    page_obj = get_page_context(
        group.posts.select_related('author', 'group'), request
    )
    all_posts_author = True
    context = {
        'group': group,
        'page_obj': page_obj,
        'all_posts_author': all_posts_author,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_count = author.posts.all().count()
    page_obj = get_page_context(
        author.posts.select_related('author', 'group'), request
    )
    is_edit = True
    title = f'Профайл пользователя {username}'
    context = {
        'title': title,
        'author': author,
        'post_count': post_count,
        'page_obj': page_obj,
        'is_edit': is_edit,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    author_post = post.author
    post_count = Post.objects.filter(author=author_post).count()
    title = f'Пост {post.text[:TEXT_SLICE]}'
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    if form.is_valid():
        comments = form.save(commit=False)
        comments.post = post
        comments.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'post_count': post_count,
        'title': title,
        'author_post': author_post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)

    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.save()
        return redirect('posts:profile', username=request.user.username)

    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post.pk)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    is_edit = True

    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.pk)

    context = {
        'is_edit': is_edit,
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comments = form.save(commit=False)
        comments.author = request.user
        comments.post = post
        comments.save()
    return redirect('posts:post_detail', post_id=post_id)
