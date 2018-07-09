from django.db import models

class Company(models.Model):
    asx_code = models.CharField(max_length=10, null=False)
    asx_code_aka = models.CharField(max_length=3, null=False)
    company_name = models.CharField(max_length=140, null=False)
    gics_industry_group = models.CharField(max_length=140, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    listing_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['asx_code_aka'], name='asx_code_aka_idx'),
        ]

    def __str__(self):
        return "%s - %s" % (self.asx_code, self.company_name)

class Announcement(models.Model):
    ticker = models.CharField(max_length=3, null=False)
    asx_date = models.DateTimeField(null=False)
    price_sensitive = models.BooleanField(default=False)
    headline = models.CharField(max_length=140, null=False)
    url = models.IntegerField(null=False)
    pages = models.IntegerField(null=False)
    filesize = models.CharField(max_length=20, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=False)

    class Meta:
        indexes = [
            models.Index(fields=['url'], name='url_idx'),
        ]

    def __str__(self):
        return "%s - %s" % (str(self.date), self.headline)
