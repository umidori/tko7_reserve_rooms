from django.contrib import admin
from .models import Room, Reservation, Building, Facility

admin.site.register(Room)
admin.site.register(Reservation)
admin.site.register(Building)
admin.site.register(Facility)
