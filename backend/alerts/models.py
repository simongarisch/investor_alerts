from django.db import models
from accounts.models import User
from announcements.models import Company, Announcement

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    price_sensitive_only = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.user, self.company)

class Alert(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    alert_sent = models.BooleanField(default=True)

    def __str__(self):
        return str(self.created_at, self.announcement)
