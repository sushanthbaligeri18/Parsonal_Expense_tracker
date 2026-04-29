from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Q
from datetime import datetime


class Profile(models.Model):
    """User Profile to store role information"""
    ROLE_CHOICES = [
        ('driver', 'Driver'),
        ('passenger', 'Passenger'),
        ('both', 'Both'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='passenger')
    phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    class Meta:
        verbose_name_plural = "Profiles"


class Ride(models.Model):
    """Ride Model for drivers to post rides"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rides_posted')
    from_location = models.CharField(max_length=255)
    to_location = models.CharField(max_length=255)
    departure_datetime = models.DateTimeField()
    arrival_datetime = models.DateTimeField()
    available_seats = models.IntegerField(validators=[MinValueValidator(1)])
    price_per_seat = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    phone_number = models.CharField(max_length=20)
    car_name = models.CharField(max_length=100, blank=True, null=True)
    car_number = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validate that arrival time is after departure time and no overlapping rides"""
        from django.core.exceptions import ValidationError
        if self.arrival_datetime <= self.departure_datetime:
            raise ValidationError('Arrival time must be after departure time.')
        
        # Check for overlapping rides for the same driver
        overlapping_rides = Ride.objects.filter(
            driver=self.driver,
            status='active'
        ).exclude(pk=self.pk).filter(
            models.Q(
                departure_datetime__lt=self.arrival_datetime,
                arrival_datetime__gt=self.departure_datetime
            )
        )
        if overlapping_rides.exists():
            raise ValidationError('You cannot create a ride during this time period because you already have a scheduled ride.')

    def save(self, *args, **kwargs):
        self.full_clean()  # This will call clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.from_location} to {self.to_location} - {self.driver.get_full_name() or self.driver.username}"

    @property
    def remaining_seats(self):
        """Calculate remaining available seats based on accepted bookings"""
        booked_seats = self.bookings.filter(status__in=['accepted', 'pending']).aggregate(
            total_seats=models.Sum('seats_booked')
        )['total_seats'] or 0
        return max(0, self.available_seats - booked_seats)

    class Meta:
        ordering = ['-departure_datetime']
        indexes = [
            models.Index(fields=['from_location']),
            models.Index(fields=['to_location']),
            models.Index(fields=['departure_datetime']),
            models.Index(fields=['status']),
        ]


class Booking(models.Model):
    """Booking Model for passengers to book rides"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='bookings')
    passenger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings_made')
    seats_booked = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.passenger.username} - {self.ride} - {self.status}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ride', 'status']),
            models.Index(fields=['passenger']),
        ]
        unique_together = ['ride', 'passenger']  # Prevent duplicate bookings
