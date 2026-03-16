from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone

class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email: raise ValueError('Please enter a valid email address.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
    email = models.EmailField('Email', unique=True)
    name = models.CharField('Name', max_length=100, blank=True, null=True)
    gender = models.CharField('Gender', max_length=10, blank=True, null=True)
    phone = models.CharField('Tel', max_length=20, blank=True, null=True)
    role = models.CharField('Role', max_length=10, default='user')
    preferred_currency = models.CharField(max_length=3, default='GBP')
    preferred_timezone = models.CharField(max_length=64, default='UTC')
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    objects = MyUserManager()

class EmailOTP(models.Model):
    
    email = models.EmailField()
    code_hash = models.CharField(max_length=255)
    purpose = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    send_ip = models.GenericIPAddressField(null=True, blank=True)
    attempt_count = models.IntegerField(default=0)
    def is_active(self):
        #check if the OTP is already used or expired.
        return self.used_at is None and timezone.now() < self.expires_at
