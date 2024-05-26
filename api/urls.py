from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import login_view, verify_user_view, registration_view, forgot_password_view, reset_password_view, google_signin_view, refresh_postcode_view, send_query_view, get_all_postcodes_view, get_cleaner_booking_cost_view, book_cleaner_view


urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/', login_view, name='login_view'),
    path('verify-user/<str:access_token>', verify_user_view, name='verify_user_view'),
    path('register/', registration_view, name='registration_view'),
    path('forgot-password/', forgot_password_view, name='forgot_password_view'),
    path('reset-password/<str:access_token>', reset_password_view, name='reset_password_view'),
    path('google-signin/', google_signin_view, name='google_signin_view'),
    path('refresh-postcode/', refresh_postcode_view, name='refresh_postcode_view'),
    path('send-query/', send_query_view, name='send_query_view'),
    path('get-all-postcodes/', get_all_postcodes_view, name='get_all_postcodes_view'),
    path('get-cleaner-booking_cost/', get_cleaner_booking_cost_view, name='get_cleaner_booking_cost_view'),
    path('book-cleaner/', book_cleaner_view, name='book_cleaner_view'),
]