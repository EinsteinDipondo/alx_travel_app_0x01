from rest_framework import serializers
from .models import Booking, Payment, Listing
from django.utils import timezone

class ListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    listing = ListingSerializer(read_only=True)
    listing_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['user', 'status', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class PaymentSerializer(serializers.ModelSerializer):
    booking = BookingSerializer(read_only=True)
    booking_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = [
            'id', 'user', 'tx_ref', 'status', 'chapa_transaction_id',
            'checkout_url', 'created_at', 'updated_at', 'payment_date',
            'error_message', 'retry_count'
        ]

class PaymentInitiateSerializer(serializers.Serializer):
    booking_id = serializers.UUIDField(required=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    return_url = serializers.URLField(required=False, allow_blank=True)
    
    def validate_booking_id(self, value):
        """Validate that booking exists and belongs to user"""
        request = self.context.get('request')
        if request and request.user:
            try:
                booking = Booking.objects.get(id=value, user=request.user)
                if booking.status != 'pending':
                    raise serializers.ValidationError(
                        "Booking is already confirmed or cancelled"
                    )
                return value
            except Booking.DoesNotExist:
                raise serializers.ValidationError("Booking not found")
        return value