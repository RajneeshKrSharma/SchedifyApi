from django.db import models
from django.utils import timezone


from django.db import models
from django.utils import timezone

class SessionDataConfig(models.Model):
    isPreAuthDataRefreshRequired = models.BooleanField(default=False)
    isPostAuthDataRefreshRequired = models.BooleanField(default=False)

    isPreAuthDataRefreshedAt = models.DateTimeField(null=True, blank=True, editable=False)
    isPostAuthDataRefreshedAt = models.DateTimeField(null=True, blank=True, editable=False)

    sessionExpiryTimeInMin = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.pk:
            old = SessionDataConfig.objects.get(pk=self.pk)
            if old.isPreAuthDataRefreshRequired != self.isPreAuthDataRefreshRequired:
                self.isPreAuthDataRefreshedAt = timezone.now()
            if old.isPostAuthDataRefreshRequired != self.isPostAuthDataRefreshRequired:
                self.isPostAuthDataRefreshedAt = timezone.now()
        else:
            if self.isPreAuthDataRefreshRequired:
                self.isPreAuthDataRefreshedAt = timezone.now()
            if self.isPostAuthDataRefreshRequired:
                self.isPostAuthDataRefreshedAt = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return "SessionDataConfig"


class Session(models.Model):
    user = models.OneToOneField('EmailIdRegistration', on_delete=models.CASCADE, related_name='session', null=True)

    preAuthSessionCreatedAt = models.DateTimeField(auto_now_add=True)
    postAuthSessionCreatedAt = models.DateTimeField(null=True, blank=True)

    preAuthSessionRefreshedAt = models.DateTimeField(null=True, blank=True)
    postAuthSessionRefreshedAt = models.DateTimeField(null=True, blank=True)

    isPreAuthDataRefreshValue = models.BooleanField(default=False)
    isPostAuthDataRefreshValue = models.BooleanField(default=False)

    def __str__(self):
        return f"Session for {self.user.emailId}"
