"""
URL configuration for rides app.
"""
from django.urls import path
from . import views

# Authentication URLs
urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]

# Dashboard URLs
urlpatterns += [
    path('dashboard/', views.dashboard, name='dashboard'),
]

# Ride Management URLs (Driver)
urlpatterns += [
    path('rides/add/', views.add_ride, name='add_ride'),
    path('rides/<int:ride_id>/', views.ride_detail, name='ride_detail'),
    path('rides/<int:ride_id>/edit/', views.edit_ride, name='edit_ride'),
    path('rides/<int:ride_id>/delete/', views.delete_ride, name='delete_ride'),
]

# Search and Booking URLs (Passenger)
urlpatterns += [
    path('search/', views.search_rides, name='search_rides'),
    path('rides/<int:ride_id>/book/', views.book_ride, name='book_ride'),
]

# Booking Management URLs
urlpatterns += [
    path('booking/<int:booking_id>/', views.booking_status, name='booking_status'),
    path('booking/<int:booking_id>/accept/', views.accept_booking, name='accept_booking'),
    path('booking/<int:booking_id>/reject/', views.reject_booking, name='reject_booking'),
]


