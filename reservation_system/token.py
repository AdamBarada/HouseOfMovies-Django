from rest_framework.authentication import TokenAuthentication

# change Token to Bearer to make it a bearer token

class BearerAuthentication(TokenAuthentication):
    keyword = 'Bearer'