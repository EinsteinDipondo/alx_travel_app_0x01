import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from listings.models import User, Listing, Booking, Review


class Command(BaseCommand):
    help = 'Seed the database with sample data for ALX Travel App'
    
    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        
        # Clear existing data
        User.objects.all().delete()
        Listing.objects.all().delete()
        Booking.objects.all().delete()
        Review.objects.all().delete()
        
        # Create users
        hosts = []
        guests = []
        
        # Create host users
        host_data = [
            {'first_name': 'John', 'last_name': 'Smith', 'email': 'john.smith@example.com', 'role': 'host'},
            {'first_name': 'Maria', 'last_name': 'Garcia', 'email': 'maria.garcia@example.com', 'role': 'host'},
            {'first_name': 'David', 'last_name': 'Johnson', 'email': 'david.johnson@example.com', 'role': 'host'},
            {'first_name': 'Sarah', 'last_name': 'Williams', 'email': 'sarah.williams@example.com', 'role': 'host'},
        ]
        
        for host_info in host_data:
            host = User.objects.create_user(
                first_name=host_info['first_name'],
                last_name=host_info['last_name'],
                email=host_info['email'],
                password='password123',
                role=host_info['role']
            )
            hosts.append(host)
            self.stdout.write(f'Created host: {host.email}')
        
        # Create guest users
        guest_data = [
            {'first_name': 'Alice', 'last_name': 'Brown', 'email': 'alice.brown@example.com'},
            {'first_name': 'Bob', 'last_name': 'Davis', 'email': 'bob.davis@example.com'},
            {'first_name': 'Carol', 'last_name': 'Miller', 'email': 'carol.miller@example.com'},
            {'first_name': 'Eve', 'last_name': 'Wilson', 'email': 'eve.wilson@example.com'},
        ]
        
        for guest_info in guest_data:
            guest = User.objects.create_user(
                first_name=guest_info['first_name'],
                last_name=guest_info['last_name'],
                email=guest_info['email'],
                password='password123',
                role='guest'
            )
            guests.append(guest)
            self.stdout.write(f'Created guest: {guest.email}')
        
        # Create listings
        listings_data = [
            {
                'host': hosts[0],
                'title': 'Cozy Apartment in Downtown',
                'description': 'A beautiful cozy apartment located in the heart of downtown with amazing city views.',
                'property_type': 'apartment',
                'price_per_night': 120.00,
                'max_guests': 4,
                'bedrooms': 2,
                'bathrooms': 1,
                'address': '123 Main Street',
                'city': 'New York',
                'country': 'USA',
                'amenities': ['WiFi', 'Kitchen', 'Air conditioning', 'TV', 'Elevator']
            },
            {
                'host': hosts[1],
                'title': 'Luxury Villa with Pool',
                'description': 'Stunning luxury villa with private pool and beautiful garden. Perfect for families.',
                'property_type': 'villa',
                'price_per_night': 350.00,
                'max_guests': 8,
                'bedrooms': 4,
                'bathrooms': 3,
                'address': '456 Beach Road',
                'city': 'Miami',
                'country': 'USA',
                'amenities': ['Pool', 'WiFi', 'Kitchen', 'Air conditioning', 'Garden', 'Parking']
            },
            {
                'host': hosts[2],
                'title': 'Modern Condo with Ocean View',
                'description': 'Modern and stylish condo with breathtaking ocean views and all amenities.',
                'property_type': 'condo',
                'price_per_night': 200.00,
                'max_guests': 6,
                'bedrooms': 3,
                'bathrooms': 2,
                'address': '789 Ocean Drive',
                'city': 'Los Angeles',
                'country': 'USA',
                'amenities': ['WiFi', 'Kitchen', 'Air conditioning', 'Balcony', 'Gym']
            },
            {
                'host': hosts[3],
                'title': 'Rustic Cabin in the Woods',
                'description': 'Peaceful cabin surrounded by nature. Perfect for a quiet getaway.',
                'property_type': 'cabin',
                'price_per_night': 90.00,
                'max_guests': 4,
                'bedrooms': 2,
                'bathrooms': 1,
                'address': '321 Forest Lane',
                'city': 'Denver',
                'country': 'USA',
                'amenities': ['Fireplace', 'Kitchen', 'Garden', 'Parking', 'BBQ']
            },
        ]
        
        listings = []
        for listing_data in listings_data:
            listing = Listing.objects.create(**listing_data)
            listings.append(listing)
            self.stdout.write(f'Created listing: {listing.title}')
        
        # Create bookings
        import datetime
        from datetime import timedelta
        
        booking_data = []
        for i, guest in enumerate(guests):
            listing = listings[i % len(listings)]
            check_in = timezone.now().date() + timedelta(days=30 * (i + 1))
            check_out = check_in + timedelta(days=random.randint(2, 7))
            total_price = (check_out - check_in).days * listing.price_per_night
            
            booking = Booking.objects.create(
                user=guest,
                listing=listing,
                check_in=check_in,
                check_out=check_out,
                total_price=total_price,
                guests=random.randint(1, listing.max_guests),
                status=random.choice(['confirmed', 'completed', 'pending']),
                special_requests='Early check-in requested' if i % 2 == 0 else ''
            )
            booking_data.append(booking)
            self.stdout.write(f'Created booking: {booking.booking_id}')
        
        # Create reviews
        review_comments = [
            'Amazing place! Would definitely stay again.',
            'Great location and very comfortable.',
            'The host was very responsive and helpful.',
            'Beautiful property with all the amenities we needed.',
            'Perfect getaway spot, highly recommended!',
            'Clean, comfortable, and great value for money.',
        ]
        
        for i, booking in enumerate(booking_data):
            if booking.status == 'completed':
                review = Review.objects.create(
                    user=booking.user,
                    listing=booking.listing,
                    booking=booking,
                    rating=random.randint(4, 5),
                    comment=random.choice(review_comments)
                )
                self.stdout.write(f'Created review: {review.review_id}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully seeded database with sample data!')
        )
        self.stdout.write(f'Created {len(hosts) + len(guests)} users')
        self.stdout.write(f'Created {len(listings)} listings')
        self.stdout.write(f'Created {len(booking_data)} bookings')
        self.stdout.write(f'Created {Review.objects.count()} reviews')
