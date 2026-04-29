from django.contrib import admin
from .models import Profile, Ride, Booking

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ('driver', 'from_location', 'to_location', 'departure_datetime', 'arrival_datetime', 'available_seats', 'status', 'created_at')
    list_filter = ('status', 'departure_datetime', 'created_at')
    search_fields = ('driver__username', 'from_location', 'to_location', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Driver Info', {
            'fields': ('driver', 'phone_number')
        }),
        ('Route', {
            'fields': ('from_location', 'from_latitude', 'from_longitude', 'to_location', 'to_latitude', 'to_longitude')
        }),
        ('Details', {
            'fields': ('departure_datetime', 'arrival_datetime', 'available_seats', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('passenger', 'ride', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('passenger__username', 'ride__from_location', 'ride__to_location')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Booking Info', {
            'fields': ('ride', 'passenger', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
