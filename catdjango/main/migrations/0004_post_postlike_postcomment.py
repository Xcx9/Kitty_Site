import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_comment_like'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='breed_comments', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.AlterField(
            model_name='like',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='breed_likes', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Заголовок')),
                ('content', models.TextField(max_length=2000, verbose_name='Содержимое')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to=settings.AUTH_USER_MODEL, verbose_name='Автор')),
            ],
            options={
                'verbose_name': 'Пост',
                'verbose_name_plural': 'Посты',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PostLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.SmallIntegerField(choices=[(1, 'Лайк'), (-1, 'Дизлайк')], verbose_name='Оценка')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_likes', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_likes', to='main.post', verbose_name='Пост')),
            ],
            options={
                'verbose_name': 'Лайк к посту',
                'verbose_name_plural': 'Лайки к постам',
                'unique_together': {('user', 'post')},
            },
        ),
        migrations.CreateModel(
            name='PostComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(max_length=1000, verbose_name='Текст')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_comments', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_comments', to='main.post', verbose_name='Пост')),
            ],
            options={
                'verbose_name': 'Комментарий к посту',
                'verbose_name_plural': 'Комментарии к постам',
                'ordering': ['created_at'],
            },
        ),
    ]
