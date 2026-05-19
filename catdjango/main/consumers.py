import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Post, PostLike, PostComment

GROUP_NAME = 'posts_feed'


class PostsConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.channel_layer.group_add(GROUP_NAME, self.channel_name)
        await self.accept()
        posts = await self.db_get_all_posts()
        await self.send(text_data=json.dumps({'type': 'initial', 'posts': posts}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(GROUP_NAME, self.channel_name)

    async def receive(self, text_data):
        user = self.scope['user']
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        action = data.get('action')

        if action == 'create_post':
            if not user.is_authenticated:
                await self.send_error('Необходимо войти в систему.')
                return
            title = data.get('title', '').strip()
            content = data.get('content', '').strip()
            if not title or not content:
                await self.send_error('Заполните заголовок и содержимое.')
                return
            if len(title) > 200 or len(content) > 2000:
                await self.send_error('Превышена максимальная длина текста.')
                return
            post = await self.db_create_post(user, title, content)
            await self.channel_layer.group_send(GROUP_NAME, {
                'type': 'ws_new_post',
                'post': post,
            })

        elif action == 'toggle_like':
            if not user.is_authenticated:
                await self.send_error('Необходимо войти в систему.')
                return
            post_id = data.get('post_id')
            value = data.get('value')
            if not post_id or value not in (1, -1):
                await self.send_error('Неверные параметры.')
                return
            result = await self.db_toggle_like(user, post_id, value)
            if result:
                await self.channel_layer.group_send(GROUP_NAME, {
                    'type': 'ws_like_update',
                    'update': result,
                    'sender': self.channel_name,
                })

        elif action == 'add_comment':
            if not user.is_authenticated:
                await self.send_error('Необходимо войти в систему.')
                return
            post_id = data.get('post_id')
            text = data.get('text', '').strip()
            if not post_id or not text:
                await self.send_error('Заполните все поля.')
                return
            if len(text) > 1000:
                await self.send_error('Комментарий слишком длинный.')
                return
            result = await self.db_add_comment(user, post_id, text)
            if result:
                await self.channel_layer.group_send(GROUP_NAME, {
                    'type': 'ws_new_comment',
                    'result': result,
                })

        elif action == 'get_comments':
            post_id = data.get('post_id')
            if not post_id:
                return
            comments = await self.db_get_comments(post_id)
            await self.send(text_data=json.dumps({
                'type': 'comments',
                'post_id': post_id,
                'comments': comments,
            }))

    # ── Обработчики групповых сообщений (вызываются у каждого клиента) ──────

    async def ws_new_post(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_post',
            'post': event['post'],
        }))

    async def ws_like_update(self, event):
        update = dict(event['update'])
        # user_vote нужен только отправителю лайка; остальным — null
        if event.get('sender') != self.channel_name:
            update['user_vote'] = None
        await self.send(text_data=json.dumps({
            'type': 'like_update',
            'update': update,
        }))

    async def ws_new_comment(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_comment',
            'result': event['result'],
        }))

    # ── Вспомогательные методы ───────────────────────────────────────────────

    async def send_error(self, message):
        await self.send(text_data=json.dumps({'type': 'error', 'message': message}))

    @database_sync_to_async
    def db_get_all_posts(self):
        user = self.scope['user']
        posts = (
            Post.objects
            .select_related('author')
            .prefetch_related('post_likes', 'post_comments')
            .all()
        )
        result = []
        for p in posts:
            user_vote = None
            if user.is_authenticated:
                pl = p.post_likes.filter(user=user).first()
                if pl:
                    user_vote = pl.value
            result.append({
                'id': p.id,
                'author': p.author.username,
                'title': p.title,
                'content': p.content,
                'created_at': p.created_at.strftime('%d.%m.%Y %H:%M'),
                'likes': p.post_likes.filter(value=PostLike.LIKE).count(),
                'dislikes': p.post_likes.filter(value=PostLike.DISLIKE).count(),
                'comments_count': p.post_comments.count(),
                'user_vote': user_vote,
            })
        return result

    @database_sync_to_async
    def db_create_post(self, user, title, content):
        post = Post.objects.create(author=user, title=title, content=content)
        return {
            'id': post.id,
            'author': post.author.username,
            'title': post.title,
            'content': post.content,
            'created_at': post.created_at.strftime('%d.%m.%Y %H:%M'),
            'likes': 0,
            'dislikes': 0,
            'comments_count': 0,
            'user_vote': None,
        }

    @database_sync_to_async
    def db_toggle_like(self, user, post_id, value):
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return None
        existing = PostLike.objects.filter(user=user, post=post).first()
        if existing:
            if existing.value == value:
                existing.delete()
            else:
                existing.value = value
                existing.save()
        else:
            PostLike.objects.create(user=user, post=post, value=value)

        user_vote = None
        ul = PostLike.objects.filter(user=user, post=post).first()
        if ul:
            user_vote = ul.value

        return {
            'post_id': post.id,
            'likes': PostLike.objects.filter(post=post, value=PostLike.LIKE).count(),
            'dislikes': PostLike.objects.filter(post=post, value=PostLike.DISLIKE).count(),
            'user_vote': user_vote,
        }

    @database_sync_to_async
    def db_add_comment(self, user, post_id, text):
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return None
        comment = PostComment.objects.create(user=user, post=post, text=text)
        return {
            'post_id': post.id,
            'comment': {
                'id': comment.id,
                'username': user.username,
                'text': comment.text,
                'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M'),
            },
            'comments_count': PostComment.objects.filter(post=post).count(),
        }

    @database_sync_to_async
    def db_get_comments(self, post_id):
        return [
            {
                'id': c.id,
                'username': c.user.username,
                'text': c.text,
                'created_at': c.created_at.strftime('%d.%m.%Y %H:%M'),
            }
            for c in PostComment.objects.filter(post_id=post_id)
                                        .select_related('user')
                                        .order_by('created_at')
        ]
