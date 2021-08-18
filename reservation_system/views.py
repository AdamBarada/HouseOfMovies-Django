import datetime
from django.db.models import Q, Count
from django.db.models.aggregates import Sum
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, filters, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import authenticate, logout

from .models import Category, Movie, Reservation, Room, Screening, Seat, SeatReserved, User, UserManager
from .serializers import CategorySerializer, MovieSerializer, ReservationSerializer, RoomSerializer, ScreeningSerializer, SeatReservedSerializer, SeatSerializer, UserSerializer
from .token import BearerAuthentication

# Create your views here.

nbTrendingMovies = 5
nbTrendingMoviesAdmin = 10
nbLoyalClients = 3

class CreateUserAPIView(APIView):   # public
    authentication_classes = [BearerAuthentication]
    permission_classes = (AllowAny,)
    def post(self, request):
        user = request.data
        serializer = UserSerializer(data=user)
        serializer.is_valid(raise_exception=True)
        userManager= UserManager()
        userManager.create_user(user['email'], user['password'], user['firstName'], user['lastName'])
        #serializer.save()
        return Response(status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes((AllowAny, ))
def customer_login(request):    # public
    data = request.data
    try:
        email = data['email']
        password = data['password']
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    user = authenticate(email=email, password=password)
    if user is not None:
        try:
            user_token = user.auth_token.key
        except:
            user_token = Token.objects.create(user=user)
        data = {'token': user_token, 'admin': user.is_admin}
        return Response(data=data, status=status.HTTP_200_OK)
    return Response(status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def profile(request):       # user
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def seats_for_screening(request, id):   # user
    screening = Screening.objects.get(id=id)
    seats = Seat.objects.filter(room__id=screening.roomId.id)
    seatResponse = []
    for s in seats:
        sr = SeatReserved.objects.filter(seatId__id=s.id, screening=screening.id).first()
        if sr != None:
            data = {'id' : s.id, 'row' : s.row, 'number' : s.number, 'taken': True}
        else:
            data = {'id' : s.id, 'row' : s.row, 'number' : s.number, 'taken': False}
        seatResponse.append(data)
    return Response(data=seatResponse, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes((IsAdminUser, ))
def screenings_for_movie(request, id):
    screenings = Screening.objects.filter(movieId__id=id)
    serializer = ScreeningSerializer(screenings, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes((AllowAny, ))
def available_screenings_for_movie(request, id):
    today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    screenings = Screening.objects.filter(movieId__id=id).filter( Q(date__gt=today.date()) | ( Q(date=today.date()) & Q(time__gte=today.time()) ))
    serializer = ScreeningSerializer(screenings, many=True)
    return Response(serializer.data)

@api_view(['GET','POST'])
@permission_classes((IsAuthenticated, ))
def reservations(request):    # user
    if request.method =='GET':
        reservations = Reservation.objects.filter(user=request.user)
        serializer = ReservationSerializer(reservations, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        data = request.data
        try:
            screeningId = data['screening']
            seatsIds = data['seats_ids']
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        screening = Screening.objects.get(id=screeningId)
        reservation = Reservation.objects.create(user=user, screeningId=screening, total=len(seatsIds)*screening.price)
        for s in seatsIds:
            seat = Seat.objects.get(id=s)
            SeatReserved.objects.create(screening=screening, seatId=seat, reservation=reservation)
        serializer = ReservationSerializer(reservation)
        return Response(serializer.data, status.HTTP_201_CREATED)

@api_view(['GET','DELETE'])
@permission_classes((IsAuthenticated, ))
def reservation_details(request, id):   # user
    if request.method == 'GET':
        reservation = Reservation.objects.filter(user=request.user, id=id)
        serializer = ReservationSerializer(reservation)
        return Response(serializer.data)
    elif request.method == 'DELETE':
        reservation = Reservation.objects.filter(user=request.user, id=id)
        reservation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CategoryViewset(viewsets.ReadOnlyModelViewSet):   # all
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    authentication_classes = [BearerAuthentication]
    permission_classes = [AllowAny]

class MovieViewset(viewsets.ModelViewSet):  # admin
    serializer_class = MovieSerializer
    queryset = Movie.objects.all()
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'director', 'cast']
    authentication_classes = [BearerAuthentication]
    permission_classes = [IsAdminUser]

class ComingSoonMovieViewSet(viewsets.ReadOnlyModelViewSet):    # public
    serializer_class = MovieSerializer
    queryset = Movie.objects.filter(releaseDate__gt = datetime.datetime.combine(datetime.date.today(), datetime.time.min).date())
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'director', 'cast']
    authentication_classes = [BearerAuthentication]
    permission_classes = [AllowAny]

class AvailableScreeningViewSet(viewsets.ReadOnlyModelViewSet): # public
    serializer_class = ScreeningSerializer
    def get_queryset(self):
        today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
        query = Screening.objects.filter( Q(date__gt=today.date()) | ( Q(date=today.date()) & Q(time__gte=today.time()) ))
        return query
    authentication_classes = [BearerAuthentication]
    permission_classes = [AllowAny]

class AvailableMovieViewSet(viewsets.ReadOnlyModelViewSet):    # public
    serializer_class = MovieSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'director', 'cast']
    def get_queryset(self):
        today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
        screenings = Screening.objects.filter( Q(date__gt=today.date()) | ( Q(date=today.date()) & Q(time__gte=today.time()) )).values_list('movieId')
        query = Movie.objects.filter(id__in = screenings)
        return query
    authentication_classes = [BearerAuthentication]
    permission_classes = [AllowAny]

class ScreeningViewset(viewsets.ModelViewSet):  # admin
    serializer_class = ScreeningSerializer
    queryset = Screening.objects.all()
    authentication_classes = [BearerAuthentication]
    permission_classes = [IsAdminUser]
    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except:
            return Response(status=status.HTTP_409_CONFLICT)
    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except:
            return Response(status=status.HTTP_409_CONFLICT)

class RoomViewset(viewsets.ModelViewSet):   # admin
    serializer_class = RoomSerializer
    queryset = Room.objects.all()
    authentication_classes = [BearerAuthentication]
    permission_classes = [IsAdminUser]

class ReservationViewSet(viewsets.ReadOnlyModelViewSet):    # admin
    serializer_class = ReservationSerializer
    queryset = Reservation.objects.all()
    authentication_classes = [BearerAuthentication]
    permission_classes = [IsAdminUser]

class OnlyUserViewSet(viewsets.ReadOnlyModelViewSet):   # admin
    serializer_class = UserSerializer
    queryset = User.objects.filter(is_staff=False, is_admin=False)
    authentication_classes = [BearerAuthentication]
    permission_classes = [IsAdminUser]

class AllUserViewSet(viewsets.ReadOnlyModelViewSet):    # admin
    serializer_class = UserSerializer
    queryset = User.objects.all()
    authentication_classes = [BearerAuthentication]
    permission_classes = [IsAdminUser]

@api_view(['GET'])  # all
def logout_view(request):
    logout(request)

@api_view(['GET'])  # public
def available_trending_movies(request):
    today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    screenings = Screening.objects.filter( Q(date__gt=today.date()) | ( Q(date=today.date()) & Q(time__gte=today.time()) )).values_list('movieId')
    query = Movie.objects.filter(id__in = screenings)
    most_watched_movies =query.annotate(count=Count('screening__reservation__seatreserved')).order_by('-count')[:nbTrendingMovies]
    serializer = MovieSerializer(most_watched_movies, many=True)
    return Response(serializer.data)

@api_view(['GET'])  # admin
@permission_classes((IsAdminUser, ))
def trending_movies(request):
    most_watched_movies = Movie.objects.annotate(count=Count('screening__reservation__seatreserved')).order_by('-count')[:nbTrendingMoviesAdmin]
    serializer = MovieSerializer(most_watched_movies, many=True)
    return Response(serializer.data)


# admin part : the dashboards and numbers 

@api_view(['GET'])
@permission_classes((IsAdminUser, ))
def number_of_movies_per_category(request):
    categories = Category.objects.all().annotate(movies_count=Count('movie'))
    response = []
    for cat in categories:
        data = {'name': cat.name, 'value': cat.movies_count}
        response.append(data)
    return Response(data=response)

@api_view(['GET'])
@permission_classes((IsAdminUser, ))
def number_of_users(request):
    nb = User.objects.filter(is_staff=False, is_admin=False).count()
    data = {'total': nb }
    return Response(data)

@api_view(['GET'])
@permission_classes((IsAdminUser, ))
def income_and_nb_reservations(request):
    totalNumber = Reservation.objects.count()
    totalIncome = Reservation.objects.aggregate(Sum('total')).values()
    data = {'totalNumber':totalNumber, 'totalIncome':totalIncome} # total income must be fixed
    return Response(data)

@api_view(['GET'])
@permission_classes((IsAdminUser, ))
def loyal_clients(request):
    clients_most_reservations= User.objects.filter(is_staff=False, is_admin=False)
    clients_most_reservations= clients_most_reservations.annotate(count=Count('reservation')).order_by('-count')[:nbLoyalClients]
    serializer = UserSerializer(clients_most_reservations, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes((IsAdminUser, ))
def seats_reserved_per_category_last_week(request):
    categories = Category.objects.all()
    response = []
    today = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    for cat in categories:
        day= today - datetime.timedelta(days=7)
        series = []
        for i in range(0,7):
            nb = SeatReserved.objects.filter(reservation__screeningId__movieId__categoriesId=cat.id).filter(reservation__date=day).count()
            data= {'name': day.date(), 'value': nb}
            series.append(data)
            day = day + datetime.timedelta(days=1)
        data={'name': cat.name, 'series': series}
        response.append(data)
    return Response(data=response)