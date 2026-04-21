from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class Room(models.Model):
    """会議室マスタ (F-18〜F-20)"""
    name     = models.CharField(max_length=100, unique=True, verbose_name='室名')
    capacity = models.PositiveIntegerField(verbose_name='収容人数')
    building = models.CharField(max_length=100, blank=True, default='', verbose_name='建物')
    floor    = models.IntegerField(null=True, blank=True, verbose_name='階数')
    is_active = models.BooleanField(default=True, verbose_name='利用可能')

    def __str__(self) -> str:
        return self.name


class Reservation(models.Model):
    room = models.ForeignKey('Room', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    title = models.CharField(max_length=200)
    participants = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    is_cancelled = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reservations"

    def __str__(self):
        return self.title