from django.db import models


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
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    reserved_by = models.CharField(max_length=100)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    purpose = models.CharField(max_length=200, blank=True)

    def __str__(self) -> str:
        return f"{self.room.name} {self.date} {self.start_time}-{self.end_time}"