from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Имя')),
                ('email', models.EmailField(max_length=254, verbose_name='Email')),
                ('subject', models.CharField(max_length=200, verbose_name='Тема')),
                ('message', models.TextField(max_length=1000, verbose_name='Сообщение')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата')),
                ('sent_to_telegram', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Обратная связь',
                'verbose_name_plural': 'Обратная связь',
                'ordering': ['-created_at'],
            },
        ),
    ]
