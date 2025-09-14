from rest_framework.authentication import SessionAuthentication

class CustomSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        # Custom CSRF enforcement logic (if needed)
        if request.path.startswith('/api/'):
            return
        super().enforce_csrf(request)
