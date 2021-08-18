from .models import Category, Movie, Reservation, Screening, Seat, SeatReserved, User
from django.contrib import admin

# Register your models here.
admin.site.register(Movie)
admin.site.register(Screening)
admin.site.register(Category)
admin.site.register(Reservation)
admin.site.register(Seat)
admin.site.register(SeatReserved)
admin.site.register(User)