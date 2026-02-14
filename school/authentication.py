from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
import requests

class ExternalUserJWTAuthentication(JWTAuthentication):

    def get_user(self, validated_token):
        user_id = validated_token.get("user_id")

        if not user_id:
            raise AuthenticationFailed("User ID not found in token")

        # Call your external user service API here
        #change in production
        print(user_id, "user id")
        try:
            response = requests.get(f"http://127.0.0.1:8001/users/{user_id}")
            response.raise_for_status()
        except requests.RequestException:
            raise AuthenticationFailed("Failed to fetch user from user service")

        user_data = response.json()

        # Create a simple user-like object
        class ExternalUser:
            def __init__(self, data):
                self.id = data.get("id")
                self.username = data.get("username")
                self.email = data.get("email")
                self.is_authenticated = True

            def __str__(self):
                return self.username or "ExternalUser"

        return ExternalUser(user_data)
