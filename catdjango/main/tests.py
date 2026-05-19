from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Post, PostLike, PostComment, Comment, Like, Feedback
import json


class PageLoadTests(TestCase):
    """Тесты доступности страниц."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Тест',
        )

    def test_home_page(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'КотоСайт')

    def test_breeds_page(self):
        response = self.client.get(reverse('breeds'))
        self.assertEqual(response.status_code, 200)

    def test_videos_page(self):
        response = self.client.get(reverse('videos'))
        self.assertEqual(response.status_code, 200)

    def test_about_page(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)

    def test_feedback_page_get(self):
        response = self.client.get(reverse('feedback'))
        self.assertEqual(response.status_code, 200)

    def test_login_page(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_register_page(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_posts_page(self):
        response = self.client.get(reverse('posts'))
        self.assertEqual(response.status_code, 200)

    def test_404_page(self):
        response = self.client.get('/nonexistent-page-xyz/')
        self.assertEqual(response.status_code, 404)

    def test_authenticated_redirect_from_login(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('login'))
        self.assertRedirects(response, reverse('home'))

    def test_authenticated_redirect_from_register(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('register'))
        self.assertRedirects(response, reverse('home'))


class AuthTests(TestCase):
    """Тесты регистрации и входа."""

    def test_register_new_user(self):
        self.client.post(reverse('register'), {
            'username': 'newuser',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'ivan@example.com',
            'password1': 'complex_pass_123',
            'password2': 'complex_pass_123',
            'favourite_cat': 'Бенгальская',
        })
        self.assertEqual(User.objects.filter(username='newuser').count(), 1)

    def test_login_valid(self):
        User.objects.create_user(username='loginuser', password='pass12345')
        response = self.client.post(reverse('login'), {
            'username': 'loginuser',
            'password': 'pass12345',
        })
        self.assertRedirects(response, reverse('home'))

    def test_login_invalid(self):
        response = self.client.post(reverse('login'), {
            'username': 'nouser',
            'password': 'wrongpass',
        })
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        User.objects.create_user(username='logoutuser', password='pass12345')
        self.client.login(username='logoutuser', password='pass12345')
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('home'))


class PostsAjaxTests(TestCase):
    """Тесты AJAX-эндпоинтов для постов."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='poster', password='pass12345'
        )
        self.client.login(username='poster', password='pass12345')

    def test_create_post(self):
        response = self.client.post(
            reverse('ajax_create_post'),
            data=json.dumps({'title': 'Тест', 'content': 'Содержимое'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertEqual(Post.objects.count(), 1)

    def test_create_post_unauthenticated(self):
        self.client.logout()
        response = self.client.post(
            reverse('ajax_create_post'),
            data=json.dumps({'title': 'Тест', 'content': 'Содержимое'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

    def test_get_posts(self):
        Post.objects.create(author=self.user, title='Пост 1', content='Текст')
        response = self.client.get(reverse('ajax_get_posts'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertEqual(len(data['posts']), 1)

    def test_toggle_like(self):
        post = Post.objects.create(author=self.user, title='П', content='Т')
        response = self.client.post(
            reverse('ajax_toggle_post_like'),
            data=json.dumps({'post_id': post.id, 'value': 1}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['likes'], 1)

    def test_add_comment(self):
        post = Post.objects.create(author=self.user, title='П', content='Т')
        response = self.client.post(
            reverse('ajax_add_post_comment'),
            data=json.dumps({'post_id': post.id, 'text': 'Комментарий'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertEqual(PostComment.objects.count(), 1)


class BreedLikesTests(TestCase):
    """Тесты лайков и комментариев к породам."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='breeduser', password='pass12345'
        )
        self.client.login(username='breeduser', password='pass12345')

    def test_toggle_breed_like(self):
        response = self.client.post(
            reverse('ajax_toggle_like'),
            data=json.dumps({'breed': 'bengal', 'value': 1}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['likes'], 1)

    def test_add_breed_comment(self):
        response = self.client.post(
            reverse('ajax_add_comment'),
            data=json.dumps({'breed': 'bengal', 'text': 'Красивая порода!'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertEqual(Comment.objects.count(), 1)

    def test_get_breed_likes(self):
        Like.objects.create(user=self.user, breed='bengal', value=Like.LIKE)
        response = self.client.get(reverse('ajax_get_likes'), {'breeds': 'bengal'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['data']['bengal']['likes'], 1)


class FeedbackTests(TestCase):
    """Тесты формы обратной связи."""

    def test_feedback_post_valid(self):
        self.client.post(reverse('feedback'), {
            'name': 'Иван',
            'email': 'ivan@example.com',
            'subject': 'Вопрос',
            'message': 'Текст сообщения',
        })
        self.assertEqual(Feedback.objects.count(), 1)

    def test_feedback_post_invalid(self):
        self.client.post(reverse('feedback'), {
            'name': '',
            'email': 'not_an_email',
            'subject': '',
            'message': '',
        })
        self.assertEqual(Feedback.objects.count(), 0)
