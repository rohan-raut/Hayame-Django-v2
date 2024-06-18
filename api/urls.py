from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import login_view, verify_user_view, registration_view, forgot_password_view, reset_password_view, google_signin_view, refresh_postcode_view, send_query_view, get_all_postcodes_view, get_cleaner_booking_cost_view, book_cleaner_view, get_booking_history_view, check_bookings_view, get_user_details_view, change_password_view, update_user_details_view, get_all_addons, get_frequency_discount_by_skill_view, get_available_slots


urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/', login_view, name='login_view'),
    path('get-user-details/', get_user_details_view, name='get_user_details_view'),
    path('verify-user/<str:access_token>', verify_user_view, name='verify_user_view'),
    path('register/', registration_view, name='registration_view'),
    path('forgot-password/', forgot_password_view, name='forgot_password_view'),
    path('reset-password/<str:access_token>', reset_password_view, name='reset_password_view'),
    path('change-password/', change_password_view, name='change_password_view'),
    path('google-signin/', google_signin_view, name='google_signin_view'),
    path('refresh-postcode/', refresh_postcode_view, name='refresh_postcode_view'),
    path('send-query/', send_query_view, name='send_query_view'),
    path('get-all-postcodes/', get_all_postcodes_view, name='get_all_postcodes_view'),
    path('get-cleaner-booking_cost/', get_cleaner_booking_cost_view, name='get_cleaner_booking_cost_view'),
    path('get-addons/', get_all_addons, name='get_all_addons'),
    path('book-cleaner/', book_cleaner_view, name='book_cleaner_view'),
    path('get-available-slots/', get_available_slots, name='get_available_slots'),
    path('get-frequency-discount-by-skill/', get_frequency_discount_by_skill_view, name='get_frequency_discount_by_skill_view'),
    path('booking-history/', get_booking_history_view, name='get_booking_history_view'),
    path('check-bookings/', check_bookings_view, name='check_bookings_view'),
    path('update/user-details/', update_user_details_view, name='update_user_details_view'),
]