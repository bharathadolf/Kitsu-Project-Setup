
try:
    import gazu
except ImportError:
    gazu = None

KITSU_HOST = "http://localhost/api"
#KITSU_HOST = "http://192.100.0.112/api"
KITSU_EMAIL = "admin@example.com"
#KITSU_EMAIL = "adolfbharath@gmail.com"
KITSU_PASSWORD = "Gattig@Veyyi#3"
#KITSU_PASSWORD = "Bharath@2026"

# Global Session Store
# Holds { 'host': ..., 'email': ..., 'password': ... } after successful login
SESSION_CREDENTIALS = None

