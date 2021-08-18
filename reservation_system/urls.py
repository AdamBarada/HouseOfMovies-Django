from django.db import router
from django.urls import path, include
from .views import AllUserViewSet, AvailableMovieViewSet, AvailableScreeningViewSet, ComingSoonMovieViewSet, CreateUserAPIView, MovieViewset, OnlyUserViewSet, ReservationViewSet, RoomViewset, ScreeningViewset, available_screenings_for_movie, available_trending_movies, income_and_nb_reservations, logout_view, loyal_clients, number_of_movies_per_category, number_of_users, profile, reservation_details, reservations, customer_login, screenings_for_movie, seats_for_screening, seats_reserved_per_category_last_week, trending_movies
# from rest_framework.authtoken.views import obtain_auth_token
from .views import CategoryViewset
from rest_framework.routers import DefaultRouter

routerPublic = DefaultRouter()
routerPublic.register('categories', CategoryViewset, basename='Categories')
routerPublic.register('movies/coming-soon', ComingSoonMovieViewSet, basename='Coming Soon Movies')
routerPublic.register('movies', AvailableMovieViewSet, basename='Available Movies')
routerPublic.register('screenings', AvailableScreeningViewSet, basename='Available Screenings')

routerAdmin = DefaultRouter()
routerAdmin.register('movies/coming-soon', ComingSoonMovieViewSet, basename='Coming Soon Movies')
routerAdmin.register('movies', MovieViewset, basename='Movies')
routerAdmin.register('screenings', ScreeningViewset, basename='Screenings')
routerAdmin.register('rooms', RoomViewset, basename='Rooms')
routerAdmin.register('reservations', ReservationViewSet, basename='Reservations')
routerAdmin.register('users/all', AllUserViewSet, basename='All Users')
routerAdmin.register('users', OnlyUserViewSet, basename='Only Users')

app_name = 'reservation_system'

urlpatterns = [
    path('logout/', logout_view, name='Logout'),
    path('public/request/sign-up/', CreateUserAPIView.as_view(), name='Sign up'), # public
    #url('login', obtain_auth_token) # does not work since we did a customized authentication
    path('token/generate-token/', customer_login, name='Login'),     # public
    path('user/request/reservations/<int:id>/', reservation_details, name='Reservation For User'),  # user
    path('user/request/reservations/', reservations, name='Reservations For User'),                 # user
    path('user/request/profile/', profile, name='User Profile'),                                    # user
    path('user/request/seats/screening/<int:id>/', seats_for_screening, name='Seats For Screening'),    # user
    path('public/request/movies/trending/', available_trending_movies, name='Available Trending Movies'),    # public
    path('public/request/screenings/movie/<int:id>/', available_screenings_for_movie, name='Available Screenings For Movie'), #public
    path('public/request/', include(routerPublic.urls), name='Public Part'),    # public
    path('admin/request/movies/trending/', trending_movies, name='Trending Movies'), # admin
    path('admin/request/movies/per-categories/', number_of_movies_per_category, name='Number Of Movies Per Category'),   # admin
    path('admin/request/users/number-users/', number_of_users, name='Number Of Users'),  # admin
    path('admin/request/users/loyal-clients/', loyal_clients, name='Number Of Users'),  # admin
    path('admin/request/reservations/total-numbers/', income_and_nb_reservations, name='Income & Nb of Reservations'), # admin
    path('admin/request/reservations/per-categories/last-week/', seats_reserved_per_category_last_week, name='Nb of Seats Reserved Last Week per Category'), # admin
    path('admin/request/screenings/movie/<int:id>/', screenings_for_movie, name='Screenings For Movie'), # admin
    path('admin/request/', include(routerAdmin.urls), name='Admin Part')        # admin
]

# to do a reservation : 
# public/request/sign-up -> token/generate-token (signup + login) == POST
# users/request/seats/screening/<int:id> (to get the seats of a screening) == GET
# users/request/reservations (to make a reservation) == POST