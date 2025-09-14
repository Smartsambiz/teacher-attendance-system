from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    print("Request headers:", dict(request.headers))
    print("Request data:", request.data)

    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user) # This creates the session

        print("User authenticated:", user.username)
        print("Session key:", request.session.session_key)
        return Response({"detail": "Login Successful", "user": {"id": user.id, "username": user.username},
                         "sessionid": request.session.session_key })
    else: 
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
    
@api_view(['POST'])
def logout_view(request):
    logout(request)
    return Response({"detail": "Logout successful."})