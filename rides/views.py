from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import models

from django.views.decorators.http import require_http_methods

from django.utils import timezone
from datetime import datetime
import json

from .models import Profile, Ride, Booking



# ============================================================================
# AUTHENTICATION VIEWS
# ============================================================================

def index(request):
    """Home page"""
    rides_count = Ride.objects.filter(status='active').count()
    drivers_count = Profile.objects.filter(role__in=['driver', 'both']).count()
    passengers_count = User.objects.count()
    
    context = {
        'rides_count': rides_count,
        'drivers_count': drivers_count,
        'passengers_count': passengers_count,
    }
    return render(request, 'index.html', context)


def register(request):
    """User registration"""
    if request.method == 'POST':
        username = request.POST.get('username')
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        role = request.POST.get('role', 'passenger')
        # Validation
        if password != password_confirm:
            messages.error(request, 'Passwords do not match!')
            return redirect('register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return redirect('register')

        if Profile.objects.filter(phone_number=phone_number).exists():
            messages.error(request, 'Phone number already exists!')
            return redirect('register')

        if len(phone_number) != 10:
            messages.error(request, 'Phone number must be 10 digits!')
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists!')
            return redirect('register')
        
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters!')
            return redirect('register')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # Save phone number in profile and set role (profile created by signal)
        profile = user.profile
        profile.role = role
        profile.phone_number = phone_number
        profile.save()
        
        messages.success(request, 'Registration successful! Please login.')
        return redirect('login')
    
    return render(request, 'auth/register.html')


def login_view(request):
    """User login"""
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')

        # Authenticate using phone number via custom backend
        user = authenticate(request, username=phone_number, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid phone number or password!')
            return redirect('login')

    return render(request, 'auth/login.html')



def logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('index')


# ============================================================================
# DASHBOARD VIEWS
# ============================================================================

@login_required(login_url='login')
def dashboard(request):
    """User dashboard - show based on role"""
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        # Create default profile if it doesn't exist
        profile = Profile.objects.create(user=request.user, role='passenger')
    
    context = {'profile': profile}
    
    if profile.role in ['driver', 'both']:
        # Show driver dashboard
        my_rides = Ride.objects.filter(driver=request.user)
        pending_bookings = Booking.objects.filter(
            ride__in=my_rides,
            status='pending'
        )
        
        # Prepare rides data with booking info
        rides_data = []
        for ride in my_rides:
            ride.accepted_count = ride.bookings.filter(status='accepted').count()
            ride.total_bookings = ride.bookings.count()
            rides_data.append(ride)
        
        context['my_rides'] = rides_data
        context['pending_bookings'] = pending_bookings
        return render(request, 'dashboard/driver_dashboard.html', context)
    
    # Show passenger dashboard
    my_bookings = Booking.objects.filter(passenger=request.user)
    context['my_bookings'] = my_bookings
    return render(request, 'dashboard/passenger_dashboard.html', context)


# ============================================================================
# RIDE MANAGEMENT VIEWS (DRIVER)
# ============================================================================

@login_required(login_url='login')
def add_ride(request):
    """Add a new ride (Driver only)"""
    # Check if user is a driver
    try:
        profile = request.user.profile
        if profile.role not in ['driver', 'both']:
            messages.error(request, 'Only drivers can add rides!')
            return redirect('dashboard')
    except Profile.DoesNotExist:
        messages.error(request, 'Please complete your profile first!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        from_location = request.POST.get('from_location')
        to_location = request.POST.get('to_location')
        departure_datetime_str = request.POST.get('departure_datetime')
        arrival_datetime_str = request.POST.get('arrival_datetime')
        available_seats = request.POST.get('available_seats')
        price_per_seat = request.POST.get('price_per_seat', 0.00)
        phone_number = request.POST.get('phone_number') or profile.phone_number  # Auto-fill from profile
        car_name = request.POST.get('car_name')
        car_number = request.POST.get('car_number')
        
        # Validation
        try:
            departure_datetime = datetime.fromisoformat(departure_datetime_str)
            if timezone.is_naive(departure_datetime):
                departure_datetime = timezone.make_aware(departure_datetime, timezone.get_current_timezone())

            arrival_datetime = datetime.fromisoformat(arrival_datetime_str)
            if timezone.is_naive(arrival_datetime):
                arrival_datetime = timezone.make_aware(arrival_datetime, timezone.get_current_timezone())

            if departure_datetime < timezone.now():
                messages.error(request, 'Departure time cannot be in the past!')
                return redirect('add_ride')
            
            if arrival_datetime <= departure_datetime:
                messages.error(request, 'Arrival time must be after departure time!')
                return redirect('add_ride')
            
            available_seats = int(available_seats)
            if available_seats < 1:
                messages.error(request, 'Available seats must be at least 1!')
                return redirect('add_ride')
            
            price_per_seat = float(price_per_seat)
            if price_per_seat < 0:
                messages.error(request, 'Price per seat cannot be negative!')
                return redirect('add_ride')
            
            # Create ride
            try:
                ride = Ride.objects.create(
                    driver=request.user,
                    from_location=from_location,
                    to_location=to_location,
                    departure_datetime=departure_datetime,
                    arrival_datetime=arrival_datetime,
                    available_seats=available_seats,
                    price_per_seat=price_per_seat,
                    phone_number=phone_number,
                    car_name=car_name,
                    car_number=car_number,
                    status='active'
                )
                
                messages.success(request, 'Ride posted successfully!')
                return redirect('ride_detail', ride_id=ride.id)
            
            except ValidationError as e:
                # Show user-friendly error message for overlapping rides
                messages.error(request, 'You cannot create a ride during this time period because you already have a scheduled ride.')
                return redirect('add_ride')
        
        except (ValueError, TypeError) as e:
            messages.error(request, f'Invalid input: {str(e)}')
            return redirect('add_ride')
        
    
    context = {
        'phone_number': profile.phone_number if profile.phone_number else ''
    }
    return render(request, 'rides/add_ride.html', context)


@login_required(login_url='login')
def ride_detail(request, ride_id):
    """View ride details"""
    ride = get_object_or_404(Ride, id=ride_id)
    bookings = Booking.objects.filter(ride=ride).select_related('passenger')

    accepted_count = bookings.filter(status='accepted').count()
    pending_count = bookings.filter(status='pending').count()
    rejected_count = bookings.filter(status='rejected').count()
    
    context = {
        'ride': ride,
        'bookings': bookings,
        'is_driver': request.user == ride.driver,
        'accepted_count': accepted_count,
        'pending_count': pending_count,
        'rejected_count': rejected_count,
    }
    return render(request, 'rides/ride_detail.html', context)


@login_required(login_url='login')
def edit_ride(request, ride_id):
    """Edit a ride (Driver only)"""
    ride = get_object_or_404(Ride, id=ride_id)
    
    # Check if user is the driver
    if request.user != ride.driver:
        messages.error(request, 'You can only edit your own rides!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        ride.from_location = request.POST.get('from_location', ride.from_location)
        ride.to_location = request.POST.get('to_location', ride.to_location)
        
        departure_datetime_str = request.POST.get('departure_datetime')
        arrival_datetime_str = request.POST.get('arrival_datetime')
        if departure_datetime_str and arrival_datetime_str:
            new_departure = datetime.fromisoformat(departure_datetime_str)
            if timezone.is_naive(new_departure):
                new_departure = timezone.make_aware(new_departure, timezone.get_current_timezone())
            ride.departure_datetime = new_departure
            
            new_arrival = datetime.fromisoformat(arrival_datetime_str)
            if timezone.is_naive(new_arrival):
                new_arrival = timezone.make_aware(new_arrival, timezone.get_current_timezone())
            ride.arrival_datetime = new_arrival

        ride.available_seats = int(request.POST.get('available_seats', ride.available_seats))
        ride.price_per_seat = float(request.POST.get('price_per_seat', ride.price_per_seat))
        if ride.price_per_seat < 0:
            messages.error(request, 'Price per seat cannot be negative!')
            return redirect('edit_ride', ride_id=ride.id)
        ride.phone_number = request.POST.get('phone_number', ride.phone_number)
        ride.car_name = request.POST.get('car_name', ride.car_name)
        ride.car_number = request.POST.get('car_number', ride.car_number)
        
        try:
            ride.save()
            messages.success(request, 'Ride updated successfully!')
            return redirect('ride_detail', ride_id=ride.id)
        except ValidationError as e:
            # Show user-friendly error message for overlapping rides
            messages.error(request, 'You cannot update this ride because you already have another scheduled ride during this time period.')
            return redirect('edit_ride', ride_id=ride.id)

    context = {'ride': ride}
    return render(request, 'rides/edit_ride.html', context)


@login_required(login_url='login')
def delete_ride(request, ride_id):
    """Delete a ride (Driver only)"""
    ride = get_object_or_404(Ride, id=ride_id)
    
    # Check if user is the driver
    if request.user != ride.driver:
        messages.error(request, 'You can only delete your own rides!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        ride.delete()
        messages.success(request, 'Ride deleted successfully!')
        return redirect('dashboard')
    
    context = {'ride': ride}
    return render(request, 'rides/delete_ride.html', context)


# ============================================================================
# SEARCH AND BOOKING VIEWS (PASSENGER)
# ============================================================================


from datetime import datetime

from django.shortcuts import render
from django.utils import timezone
from .models import Ride

def search_rides(request):
    # Start with active + future rides
    rides = Ride.objects.filter(
        status='active',
        departure_datetime__gte=timezone.now()
    ).order_by('departure_datetime')

    # Get values
    from_location = request.GET.get('from_location', '').strip()
    to_location = request.GET.get('to_location', '').strip()
    date_str = request.GET.get('date', '').strip()

    # Apply filters
    if from_location:
        rides = rides.filter(from_location__icontains=from_location)

    if to_location:
        rides = rides.filter(to_location__icontains=to_location)

    if date_str:
        rides = rides.filter(departure_datetime__date=date_str)

    # Filter out rides with 0 remaining seats
    available_rides = [ride for ride in rides if ride.remaining_seats > 0]

    # Send to template
    context = {
        'rides': available_rides,
        'from_location': from_location,
        'to_location': to_location,
        'date': date_str,
        'search_performed': bool(from_location or to_location or date_str),
        'results_count': len(available_rides),
        'search_info': f"{from_location} → {to_location} {date_str}",
    }

    return render(request, 'rides/search_rides.html', context)


@login_required(login_url='login')
def book_ride(request, ride_id):
    """Book a ride (Passenger only)"""
    ride = get_object_or_404(Ride, id=ride_id)
    
    # Check if user already booked this ride
    if Booking.objects.filter(ride=ride, passenger=request.user).exists():
        messages.error(request, 'You have already booked this ride!')
        return redirect('ride_detail', ride_id=ride.id)
    
    # Check if ride has available seats
    remaining_seats = ride.remaining_seats
    
    if remaining_seats <= 0:
        messages.error(request, 'No seats available in this ride!')
        return redirect('ride_detail', ride_id=ride.id)
    
    if request.method == 'POST':
        seats_requested = int(request.POST.get('seats_booked', 1))
        
        # Validate seats requested
        if seats_requested < 1:
            messages.error(request, 'You must book at least 1 seat!')
            return redirect('book_ride', ride_id=ride.id)
        
        if seats_requested > remaining_seats:
            messages.error(request, f'Only {remaining_seats} seats available!')
            return redirect('book_ride', ride_id=ride.id)
        
        # Create booking
        booking = Booking.objects.create(
            ride=ride,
            passenger=request.user,
            seats_booked=seats_requested,
            status='pending'
        )
        
        messages.success(request, f'Booking request sent for {seats_requested} seat{"s" if seats_requested > 1 else ""}! Wait for driver approval.')
        return redirect('booking_status', booking_id=booking.id)
    
    context = {'ride': ride}
    return render(request, 'bookings/book_ride.html', context)


# ============================================================================
# BOOKING MANAGEMENT VIEWS
# ============================================================================

@login_required(login_url='login')
def booking_status(request, booking_id):
    """View booking status"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if user has permission to view this booking
    if request.user != booking.passenger and request.user != booking.ride.driver:
        messages.error(request, 'You do not have permission to view this booking!')
        return redirect('dashboard')
    
    context = {'booking': booking}
    return render(request, 'bookings/booking_status.html', context)


@login_required(login_url='login')
def accept_booking(request, booking_id):
    """Accept a booking (Driver only)"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if user is the driver
    if request.user != booking.ride.driver:
        messages.error(request, 'Only the driver can accept bookings!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        booking.status = 'accepted'
        booking.save()
        messages.success(request, 'Booking accepted!')
        return redirect('ride_detail', ride_id=booking.ride.id)
    
    # Check if accepting this booking would fill all seats
    accepted_seats = booking.ride.bookings.filter(status='accepted').aggregate(total=models.Sum('seats_booked'))['total'] or 0
    will_fill_seats = (accepted_seats + booking.seats_booked) >= booking.ride.available_seats
    
    context = {'booking': booking, 'action': 'accept', 'will_fill_seats': will_fill_seats}
    return render(request, 'bookings/confirm_action.html', context)


@login_required(login_url='login')
def reject_booking(request, booking_id):
    """Reject a booking (Driver only)"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if user is the driver
    if request.user != booking.ride.driver:
        messages.error(request, 'Only the driver can reject bookings!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        booking.status = 'rejected'
        booking.save()
        messages.success(request, 'Booking rejected!')
        return redirect('ride_detail', ride_id=booking.ride.id)
    
    context = {'booking': booking, 'action': 'reject'}
    return render(request, 'bookings/confirm_action.html', context)


