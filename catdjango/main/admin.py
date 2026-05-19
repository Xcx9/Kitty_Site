from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Feedback, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = 'Профиль'
    verbose_name_plural = 'Профиль'


class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_favourite_cat', 'date_joined']

    def get_favourite_cat(self, obj):
        return obj.profile.favourite_cat if hasattr(obj, 'profile') else '—'
    get_favourite_cat.short_description = 'Любимый вид кошек'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'favourite_cat']
    search_fields = ['user__username', 'user__email', 'favourite_cat']


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'created_at', 'sent_to_telegram']
    list_filter = ['sent_to_telegram', 'created_at']
    search_fields = ['name', 'email', 'subject']
    readonly_fields = ['created_at', 'sent_to_telegram']
