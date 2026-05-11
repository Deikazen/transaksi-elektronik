import sys
from backend.routers.auth import RegisterRequest, LoginRequest
from backend.models import RoleEnum

try:
    print("Testing RegisterRequest")
    r = RegisterRequest(username="Test User", email="test@test.com", password="password123", role="kasir")
    print(r)
except Exception as e:
    print("Error:", e)

try:
    print("Testing LoginRequest")
    l = LoginRequest(username="Test User", password="password123")
    print(l)
except Exception as e:
    print("Error:", e)
