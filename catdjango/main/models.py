from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='Пользователь')
    favourite_cat = models.CharField(max_length=50, blank=True, verbose_name='Любимый вид кошек')

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f'Профиль: {self.user.username}'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


class Feedback(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя')
    email = models.EmailField(verbose_name='Email')
    subject = models.CharField(max_length=200, verbose_name='Тема')
    message = models.TextField(max_length=1000, verbose_name='Сообщение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')
    sent_to_telegram = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Обратная связь'
        verbose_name_plural = 'Обратная связь'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} — {self.subject}'


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='breed_comments', verbose_name='Пользователь')
    breed = models.CharField(max_length=100, verbose_name='Порода')
    text = models.TextField(max_length=500, verbose_name='Текст')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    class Meta:
        verbose_name = 'Комментарий к породе'
        verbose_name_plural = 'Комментарии к породам'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} → {self.breed}'


class Like(models.Model):
    LIKE = 1
    DISLIKE = -1
    VOTE_CHOICES = [(LIKE, 'Лайк'), (DISLIKE, 'Дизлайк')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='breed_likes', verbose_name='Пользователь')
    breed = models.CharField(max_length=100, verbose_name='Порода')
    value = models.SmallIntegerField(choices=VOTE_CHOICES, verbose_name='Оценка')

    class Meta:
        verbose_name = 'Лайк к породе'
        verbose_name_plural = 'Лайки к породам'
        unique_together = ('user', 'breed')

    def __str__(self):
        return f'{self.user.username} {"👍" if self.value == 1 else "👎"} {self.breed}'


# ─── Посты ────────────────────────────────────────────────────────────────────

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts', verbose_name='Автор')
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    content = models.TextField(max_length=2000, verbose_name='Содержимое')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.author.username}: {self.title}'

    @property
    def likes_count(self):
        return self.post_likes.filter(value=PostLike.LIKE).count()

    @property
    def dislikes_count(self):
        return self.post_likes.filter(value=PostLike.DISLIKE).count()

    @property
    def comments_count(self):
        return self.post_comments.count()


class PostLike(models.Model):
    LIKE = 1
    DISLIKE = -1
    VOTE_CHOICES = [(LIKE, 'Лайк'), (DISLIKE, 'Дизлайк')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes', verbose_name='Пользователь')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_likes', verbose_name='Пост')
    value = models.SmallIntegerField(choices=VOTE_CHOICES, verbose_name='Оценка')

    class Meta:
        verbose_name = 'Лайк к посту'
        verbose_name_plural = 'Лайки к постам'
        unique_together = ('user', 'post')

    def __str__(self):
        return f'{self.user.username} {"👍" if self.value == 1 else "👎"} пост #{self.post_id}'


class PostComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comments', verbose_name='Пользователь')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_comments', verbose_name='Пост')
    text = models.TextField(max_length=1000, verbose_name='Текст')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    class Meta:
        verbose_name = 'Комментарий к посту'
        verbose_name_plural = 'Комментарии к постам'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.user.username} → пост #{self.post_id}'
