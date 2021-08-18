from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.db.models import Q
import datetime
import base64

# models for authentication


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, firstName=None, lastName=None):
        if not email:
            raise ValueError('The given email must be set')
        user_model = get_user_model()
        user = user_model(email=self.normalize_email(email))
        #user= self.model(email = self.normalize_email(email))
        user.firstName = firstName
        user.lastName = lastName
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, firstName=None, lastName=None):
        user = self.create_user(email=self.normalize_email(
            email), password=password, firstName=firstName, lastName=lastName)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=40, unique=True)
    firstName = models.CharField(max_length=30, blank=True)
    lastName = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['firstName', 'lastName']

    def __str__(self) -> str:
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label: str) -> bool:
        return True

    @property
    def nbReservations(self):
        return setNbReservationsForUser(self)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

# models for database of the reservation system


class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "categories"
        db_table = "categories"


class Movie(models.Model):
    title = models.CharField(max_length=100)
    director = models.CharField(max_length=100)
    cast = models.CharField(max_length=255, null=True)
    duration = models.IntegerField()
    description = models.TextField(null=True)
    image = models.TextField(null=True)
    landscape = models.TextField(null=True)
    trailer = models.CharField(max_length=255, null=True)
    releaseDate = models.DateField()
    categoriesId = models.ManyToManyField(Category)

    @property
    def categories(self):
        return self.categoriesId.all()

    @property
    def status(self):
        return setStatusToMovie(self)

    @property
    def viewers(self):
        return int(setViewersToMovie(self))

    class Meta:
        db_table = "movies"
        ordering = ["-releaseDate"]


class Room(models.Model):
    name = models.CharField(max_length=100)
    nbRows = models.IntegerField()
    nbColumns = models.IntegerField()

    class Meta:
        db_table = "rooms"


class Seat(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    row = models.IntegerField()
    number = models.IntegerField()

    class Meta:
        db_table = "seats"


class Screening(models.Model):
    movieId = models.ForeignKey(Movie, on_delete=models.CASCADE)
    roomId = models.ForeignKey(Room, on_delete=models.CASCADE)
    price = models.FloatField()
    date = models.DateField()
    time = models.TimeField()

    @property
    def status(self):
        return setStatusToScreening(self)

    @property
    def movie(self):
        return self.movieId

    @property
    def room(self):
        return self.roomId

    class Meta:
        db_table = "screenings"
        ordering = ["date", "time"]


class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    screeningId = models.ForeignKey(Screening, on_delete=models.CASCADE)
    total = models.FloatField()
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)

    @property
    def status(self):
        return setStatusToScreening(self.screeningId)

    @property
    def screening(self):
        return self.screeningId

    @property
    def seats_reserved(self):
        return seatReservedForReservation(self)

    class Meta:
        db_table = "reservations"
        ordering = ["date", "time"]


class SeatReserved(models.Model):
    screening = models.ForeignKey(Screening, on_delete=models.CASCADE)
    seatId = models.ForeignKey(Seat, on_delete=models.CASCADE)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)

    @property
    def seat(self):
        return Seat.objects.get(id=self.seatId.id)

    class Meta:
        db_table = "seats_reserved"
        verbose_name_plural = "seats reserved"

# methods to add info (properties) to models


def setStatusToMovie(movie):
    today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    query = Screening.objects.filter(movieId=movie.id)
    query = query.filter(Q(date__gt=today.date()) | (
        Q(date=today.date()) & Q(time__gte=today.time())))
    if query.count() > 0:
        return 'AVAILABLE'
    return 'NOT_AVAILABLE'


def setStatusToScreening(screening):
    today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    if screening.date > today.date():
        return 'AVAILABLE'
    if screening.date == today.date() and screening.time >= today.time():
        return 'AVAILABLE'
    return 'NOT_AVAILABLE'


def setViewersToMovie(movie):
    return SeatReserved.objects.filter(screening__movieId=movie.id).count()


def seatReservedForReservation(reservation):
    return SeatReserved.objects.filter(reservation__id=reservation.id)


def setNbReservationsForUser(user):
    return Reservation.objects.filter(user=user).count()

# signals


# after creating a room, automatically create seats
@receiver(post_save, sender=Room)
def create_seats(sender, instance=None, created=False, **kwargs):
    if created:
        i = 0
        while i != instance.nbRows:
            i = i + 1
            j = 0
            while j != instance.nbColumns:
                j = j + 1
                seat = Seat(room=instance, row=i, number=j)
                seat.save()


# check if there is another screening in the same room at the same time
@receiver(pre_save, sender=Screening)
def check_timing(sender, instance=None, **kwargs):
    screenings = Screening.objects.filter(
        date=instance.date, roomId=instance.roomId)
    if screenings.count() != 0:
        start = datetime.timedelta(
            hours=instance.time.hour, minutes=instance.time.minute)
        end = start + datetime.timedelta(minutes=instance.movieId.duration)
        for s in screenings:
            start2 = datetime.timedelta(
                hours=s.time.hour, minutes=s.time.minute)
            end2 = start2 + datetime.timedelta(minutes=s.movieId.duration)
            if start == start2:
                raise Exception('conflict in time')
            if end == end2:
                raise Exception('conflict in time')
            if start >= start2 and start < end2:
                raise Exception('conflict in time')
            if end >= start2 and end < end2:
                raise Exception('conflict in time')
            if start < start2 and end > end2:
                raise Exception('conflict in time')


# receiver for adding a movie pre_save : base64->file for image and landscape
@receiver(pre_save, sender=Movie)
def save_images(sender, instance=None, **kwargs):
    if instance.image != '' and instance.image is not None:
        if ';base64,' in instance.image:
            format, imgstr = instance.image.split(';base64,')
            ext = format.split('/')[-1]
            name = str(instance.id) + 'Image.' + ext
            file = open('reservation_system/static/'+name, 'wb')
            file.write(base64.b64decode(imgstr))
            file.close()
            instance.image = 'images/' + name
    else:
        movie = Movie.objects.filter(pk=instance.id).first()
        if movie is not None:
            instance.image = movie.image
    if instance.landscape != '' and instance.landscape is not None:
        if ';base64,' in instance.landscape:
            format, imgstr = instance.landscape.split(';base64,')
            ext = format.split('/')[-1]
            name = str(instance.id) + 'Landscape.' + ext
            file = open('reservation_system/static/'+name, 'wb')
            file.write(base64.b64decode(imgstr))
            file.close()
            instance.landscape = 'images/' + name
    else:
        movie = Movie.objects.filter(pk=instance.id).first()
        if movie is not None:
            instance.landscape = movie.landscape