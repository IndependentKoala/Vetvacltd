from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin


class CustomUserAdmin(BaseUserAdmin):
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'date_joined')


class CustomGroupAdmin(BaseGroupAdmin):
    search_fields = ('name',)
    list_filter = ('name',)
    list_display = ('name',)


# Unregister the default User and Group admin
admin.site.unregister(User)
admin.site.unregister(Group)

# Register with enhanced search
admin.site.register(User, CustomUserAdmin)
admin.site.register(Group, CustomGroupAdmin)
