import json
import requests
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from .forms import RegisterForm, LoginForm, FeedbackForm
from .models import Comment, Like, Post, PostLike, PostComment


def page_not_found_view(request, *args, **kwargs):
    return render(request, 'main/404.html', status=404)


def home(request):
    return render(request, 'main/home.html')


def breeds(request):
    return render(request, 'main/breeds.html')


def videos(request):
    return render(request, 'main/videos.html')


def about(request):
    return render(request, 'main/about.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            favourite_cat = form.cleaned_data.get('favourite_cat', '')
            if hasattr(user, 'profile'):
                user.profile.favourite_cat = favourite_cat
                user.profile.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.first_name}!')
            return redirect('home')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = RegisterForm()

    return render(request, 'main/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.first_name or user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Неверный логин или пароль.')
    else:
        form = LoginForm()

    return render(request, 'main/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


def feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            token = settings.TELEGRAM_BOT_TOKEN
            chat_id = settings.TELEGRAM_CHAT_ID

            if token and chat_id:
                text = (
                    f'*Новое сообщение с сайта*\n\n'
                    f'*Имя:* {feedback.name}\n'
                    f'*Email:* {feedback.email}\n'
                    f'*Тема:* {feedback.subject}\n\n'
                    f'*Сообщение:*\n{feedback.message}'
                )
                try:
                    resp = requests.post(
                        f'https://api.telegram.org/bot{token}/sendMessage',
                        json={'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'},
                        timeout=5
                    )
                    feedback.sent_to_telegram = resp.json().get('ok', False)
                except Exception:
                    pass

            feedback.save()
            messages.success(request, 'Сообщение отправлено! Мы свяжемся с вами в ближайшее время.')
            return redirect('feedback')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = FeedbackForm()

    return render(request, 'main/feedback.html', {'form': form})


# Страница постов

def posts_view(request):
    return render(request, 'main/posts.html')


# AJAX: Посты
def _serialize_post(post, user):
    user_vote = None
    if user.is_authenticated:
        pl = PostLike.objects.filter(user=user, post=post).first()
        if pl:
            user_vote = pl.value
    return {
        'id': post.id,
        'author': post.author.username,
        'title': post.title,
        'content': post.content,
        'created_at': post.created_at.strftime('%d.%m.%Y %H:%M'),
        'likes': post.post_likes.filter(value=PostLike.LIKE).count(),
        'dislikes': post.post_likes.filter(value=PostLike.DISLIKE).count(),
        'comments_count': post.post_comments.count(),
        'user_vote': user_vote,
    }


@require_POST
def ajax_create_post(request):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Необходимо войти в систему.'}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Неверный формат данных.'}, status=400)

    title = data.get('title', '').strip()
    content = data.get('content', '').strip()

    if not title or not content:
        return JsonResponse({'ok': False, 'error': 'Заполните заголовок и содержимое.'}, status=400)
    if len(title) > 200:
        return JsonResponse({'ok': False, 'error': 'Заголовок слишком длинный (макс. 200 симв.).'}, status=400)
    if len(content) > 2000:
        return JsonResponse({'ok': False, 'error': 'Содержимое слишком длинное (макс. 2000 симв.).'}, status=400)

    post = Post.objects.create(author=request.user, title=title, content=content)
    return JsonResponse({'ok': True, 'post': _serialize_post(post, request.user)})


@require_GET
def ajax_get_posts(request):
    since_id = int(request.GET.get('since_id', 0))
    qs = Post.objects.select_related('author').prefetch_related('post_likes', 'post_comments')
    if since_id:
        qs = qs.filter(id__gt=since_id)
    posts = [_serialize_post(p, request.user) for p in qs]
    return JsonResponse({'ok': True, 'posts': posts})


@require_GET
def ajax_get_posts_updates(request):
    post_ids_raw = request.GET.get('ids', '')
    try:
        post_ids = [int(x) for x in post_ids_raw.split(',') if x.strip()]
    except ValueError:
        return JsonResponse({'ok': False, 'error': 'Неверные id.'}, status=400)

    result = {}
    for post in Post.objects.filter(id__in=post_ids).prefetch_related('post_likes', 'post_comments'):
        user_vote = None
        if request.user.is_authenticated:
            pl = PostLike.objects.filter(user=request.user, post=post).first()
            if pl:
                user_vote = pl.value
        result[post.id] = {
            'likes': post.post_likes.filter(value=PostLike.LIKE).count(),
            'dislikes': post.post_likes.filter(value=PostLike.DISLIKE).count(),
            'comments_count': post.post_comments.count(),
            'user_vote': user_vote,
        }
    return JsonResponse({'ok': True, 'data': result})


@require_POST
def ajax_toggle_post_like(request):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Необходимо войти в систему.'}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Неверный формат данных.'}, status=400)

    post_id = data.get('post_id')
    value = data.get('value')

    if not post_id or value not in (1, -1):
        return JsonResponse({'ok': False, 'error': 'Неверные параметры.'}, status=400)

    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Пост не найден.'}, status=404)

    existing = PostLike.objects.filter(user=request.user, post=post).first()
    if existing:
        if existing.value == value:
            existing.delete()
        else:
            existing.value = value
            existing.save()
    else:
        PostLike.objects.create(user=request.user, post=post, value=value)

    user_vote = None
    ul = PostLike.objects.filter(user=request.user, post=post).first()
    if ul:
        user_vote = ul.value

    return JsonResponse({
        'ok': True,
        'post_id': post.id,
        'likes': post.post_likes.filter(value=PostLike.LIKE).count(),
        'dislikes': post.post_likes.filter(value=PostLike.DISLIKE).count(),
        'user_vote': user_vote,
    })


@require_POST
def ajax_add_post_comment(request):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Необходимо войти в систему.'}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Неверный формат данных.'}, status=400)

    post_id = data.get('post_id')
    text = data.get('text', '').strip()

    if not post_id or not text:
        return JsonResponse({'ok': False, 'error': 'Заполните все поля.'}, status=400)
    if len(text) > 1000:
        return JsonResponse({'ok': False, 'error': 'Комментарий слишком длинный.'}, status=400)

    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Пост не найден.'}, status=404)

    comment = PostComment.objects.create(user=request.user, post=post, text=text)
    return JsonResponse({
        'ok': True,
        'comment': {
            'id': comment.id,
            'username': comment.user.username,
            'text': comment.text,
            'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M'),
        },
        'comments_count': post.post_comments.count(),
    })


@require_GET
def ajax_get_post_comments(request):
    post_id = request.GET.get('post_id')
    since_id = int(request.GET.get('since_id', 0))

    if not post_id:
        return JsonResponse({'ok': False, 'error': 'Не указан post_id.'}, status=400)

    qs = PostComment.objects.filter(post_id=post_id).select_related('user')
    if since_id:
        qs = qs.filter(id__gt=since_id)

    comments = [
        {
            'id': c.id,
            'username': c.user.username,
            'text': c.text,
            'created_at': c.created_at.strftime('%d.%m.%Y %H:%M'),
        }
        for c in qs.order_by('created_at')
    ]
    return JsonResponse({'ok': True, 'comments': comments})


# AJAX: Комментарии к породам

@require_POST
def ajax_add_comment(request):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Необходимо войти в систему.'}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Неверный формат данных.'}, status=400)

    breed = data.get('breed', '').strip()
    text = data.get('text', '').strip()

    if not breed or not text:
        return JsonResponse({'ok': False, 'error': 'Заполните все поля.'}, status=400)
    if len(text) > 500:
        return JsonResponse({'ok': False, 'error': 'Комментарий слишком длинный.'}, status=400)

    comment = Comment.objects.create(user=request.user, breed=breed, text=text)
    return JsonResponse({
        'ok': True,
        'comment': {
            'id': comment.id,
            'username': comment.user.username,
            'breed': comment.breed,
            'text': comment.text,
            'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M'),
        }
    })


@require_GET
def ajax_get_comments(request):
    breed = request.GET.get('breed', '').strip()
    since_id = int(request.GET.get('since_id', 0))

    qs = Comment.objects.select_related('user')
    if breed:
        qs = qs.filter(breed=breed)
    if since_id:
        qs = qs.filter(id__gt=since_id)

    comments = [
        {
            'id': c.id,
            'username': c.user.username,
            'breed': c.breed,
            'text': c.text,
            'created_at': c.created_at.strftime('%d.%m.%Y %H:%M'),
        }
        for c in qs.order_by('created_at')
    ]
    return JsonResponse({'ok': True, 'comments': comments})


# AJAX: Лайки к породам

@require_POST
def ajax_toggle_like(request):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Необходимо войти в систему.'}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Неверный формат данных.'}, status=400)

    breed = data.get('breed', '').strip()
    value = data.get('value')

    if not breed or value not in (1, -1):
        return JsonResponse({'ok': False, 'error': 'Неверные параметры.'}, status=400)

    existing = Like.objects.filter(user=request.user, breed=breed).first()
    if existing:
        if existing.value == value:
            existing.delete()
        else:
            existing.value = value
            existing.save()
    else:
        Like.objects.create(user=request.user, breed=breed, value=value)

    likes = Like.objects.filter(breed=breed, value=Like.LIKE).count()
    dislikes = Like.objects.filter(breed=breed, value=Like.DISLIKE).count()

    user_vote = None
    user_like = Like.objects.filter(user=request.user, breed=breed).first()
    if user_like:
        user_vote = user_like.value

    return JsonResponse({
        'ok': True,
        'breed': breed,
        'likes': likes,
        'dislikes': dislikes,
        'user_vote': user_vote,
    })


@require_GET
def ajax_get_likes(request):
    breeds_param = request.GET.get('breeds', '')
    breed_list = [b.strip() for b in breeds_param.split(',') if b.strip()]

    result = {}
    for breed in breed_list:
        likes = Like.objects.filter(breed=breed, value=Like.LIKE).count()
        dislikes = Like.objects.filter(breed=breed, value=Like.DISLIKE).count()
        user_vote = None
        if request.user.is_authenticated:
            ul = Like.objects.filter(user=request.user, breed=breed).first()
            if ul:
                user_vote = ul.value
        result[breed] = {'likes': likes, 'dislikes': dislikes, 'user_vote': user_vote}

    return JsonResponse({'ok': True, 'data': result})
