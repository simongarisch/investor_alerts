from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()

class UserAdmin(admin.ModelAdmin):
    search_fields = ['email']
    class Meta:
        model = User


admin.site.register(User, UserAdmin)
