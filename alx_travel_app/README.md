# ALX Travel App API

This project provides RESTful API endpoints for managing property listings and bookings.

## API Endpoints

### Listings
- `GET /api/listings/` - List all listings
- `POST /api/listings/` - Create a new listing
- `GET /api/listings/{id}/` - Retrieve a specific listing
- `PUT /api/listings/{id}/` - Update a listing
- `PATCH /api/listings/{id}/` - Partially update a listing
- `DELETE /api/listings/{id}/` - Delete a listing

### Bookings
- `GET /api/bookings/` - List all bookings
- `POST /api/bookings/` - Create a new booking
- `GET /api/bookings/{id}/` - Retrieve a specific booking
- `PUT /api/bookings/{id}/` - Update a booking
- `PATCH /api/bookings/{id}/` - Partially update a booking
- `DELETE /api/bookings/{id}/` - Delete a booking

## API Documentation

Swagger documentation is available at:
- Swagger UI: `/swagger/`
- ReDoc: `/redoc/`

## Testing with Postman

### Setup
1. Start the Django development server
2. Open Postman
3. Set the base URL: `http://localhost:8000/api/`

### Test Examples

#### Create a Listing (POST)