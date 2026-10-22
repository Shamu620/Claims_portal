from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class MoreUserDetails(models.Model):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Sub-Admin', 'Sub-Admin'),
    ]
    details = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='more_user_details')
    role = models.CharField(max_length=10, null=False, blank=False, choices=ROLE_CHOICES)
    pf = models.CharField(max_length=10, null=False, blank=False)



class Otp(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(null=False, blank=False, db_index=True)
    otp = models.CharField(max_length=6, null=False, blank=False)
    creation_time = models.DateTimeField(auto_now_add=True, null=False, blank=False)

    def is_expired(self):
        """Returns True if the OTP is older than 10 minutes, otherwise False."""
        return (timezone.now() - self.creation_time) > timedelta(minutes=10)

    def clear_if_expired(self):
        """Clears the OTP in the database if it has expired."""
        if self.is_expired() and self.otp:
            self.otp = ""
            self.save(update_fields=['otp'])