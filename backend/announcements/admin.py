from django.contrib import admin

from .models import Company, Announcement

admin.site.register(Company)
admin.site.register(Announcement)
