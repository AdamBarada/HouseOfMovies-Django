from rest_framework import serializers
from.models import Reservation, Room, Screening, Seat, SeatReserved, User, Category, Movie

class UserSerializer(serializers.ModelSerializer):
    date_joined = serializers.ReadOnlyField()
    nbReservations = serializers.IntegerField(read_only=True)
    class Meta(object):
        model = User
        fields = ('id', 'email', 'firstName', 'lastName', 'is_admin',
                  'date_joined', 'password', 'nbReservations')
        extra_kwargs = {'password': {'write_only': True}}

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class MovieSerializer(serializers.ModelSerializer):
    status = serializers.CharField(max_length = 100, read_only = True)
    categories = CategorySerializer(many = True, read_only=True)
    viewers = serializers.IntegerField(read_only=True)
    class Meta:
        model = Movie
        fields = '__all__'
        extra_kwargs = {'categoriesId': {'write_only': True}}

class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = '__all__'

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'

class ScreeningSerializer(serializers.ModelSerializer):
    status = serializers.CharField(max_length = 100, read_only=True)
    movie = MovieSerializer(read_only=True)
    room = RoomSerializer(read_only=True)
    class Meta:
        model = Screening
        fields = '__all__'
        extra_kwargs = {'movieId': {'write_only': True}, 'roomId': {'write_only': True}}

class SeatReservedSerializer(serializers.ModelSerializer):
    seat = SeatSerializer()
    class Meta:
        model = SeatReserved
        fields = '__all__'

class ReservationSerializer(serializers.ModelSerializer):
    status = serializers.CharField(max_length = 100, read_only=True)
    screening = ScreeningSerializer(read_only=True)
    seats_reserved = SeatReservedSerializer(many = True, read_only = True)
    class Meta:
        model = Reservation
        fields = '__all__'
