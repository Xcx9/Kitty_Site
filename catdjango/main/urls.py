from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('breeds/', views.breeds, name='breeds'),
    path('videos/', views.videos, name='videos'),
    path('about/', views.about, name='about'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('feedback/', views.feedback_view, name='feedback'),
    path('posts/', views.posts_view, name='posts'),

    # AJAX — Посты
    path('ajax/post/create/', views.ajax_create_post, name='ajax_create_post'),
    path('ajax/posts/', views.ajax_get_posts, name='ajax_get_posts'),
    path('ajax/posts/updates/', views.ajax_get_posts_updates, name='ajax_get_posts_updates'),
    path('ajax/post/like/', views.ajax_toggle_post_like, name='ajax_toggle_post_like'),
    path('ajax/post/comment/add/', views.ajax_add_post_comment, name='ajax_add_post_comment'),
    path('ajax/post/comments/', views.ajax_get_post_comments, name='ajax_get_post_comments'),

    # AJAX — Породы
    path('ajax/comment/add/', views.ajax_add_comment, name='ajax_add_comment'),
    path('ajax/comments/', views.ajax_get_comments, name='ajax_get_comments'),
    path('ajax/like/toggle/', views.ajax_toggle_like, name='ajax_toggle_like'),
    path('ajax/likes/', views.ajax_get_likes, name='ajax_get_likes'),

    re_path(r'^.*$', views.page_not_found_view),
]
