import requests

resp = requests.post(
    'http://127.0.0.1:8000/auth/register',
    json={
        'email': 'testuser+ai@example.com',
        'password': 'testpass123',
        'full_name': 'Test User'
    }
)
print('status', resp.status_code)
print(resp.text)
