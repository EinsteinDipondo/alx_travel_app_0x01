from django.db import models
from django.conf import settings
import uuid
from django.utils import timezone

class Booking(models.Model):
    """Booking model (assuming it exists)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    listing = models.ForeignKey('Listing', on_delete=models.CASCADE)
    check_in = models.DateField()
    check_out = models.DateField()
    number_of_guests = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
            ('cancelled', 'Cancelled'),
            ('completed', 'Completed')
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Booking {self.id} - {self.user.email}"

class Payment(models.Model):
    """Payment model to store payment information"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('chapa', 'Chapa'),
        ('telebirr', 'Telebirr'),
        ('bank', 'Bank Transfer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Payment Details
    tx_ref = models.CharField(max_length=100, unique=True, editable=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='ETB')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='chapa')
    
    # Status Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    chapa_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    checkout_url = models.URLField(max_length=500, blank=True, null=True)
    
    # Customer Information
    customer_email = models.EmailField()
    customer_first_name = models.CharField(max_length=100)
    customer_last_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Metadata
    description = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tx_ref']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Payment {self.tx_ref} - {self.amount} {self.currency} - {self.status}"
    
    def save(self, *args, **kwargs):
        # Generate unique transaction reference if not set
        if not self.tx_ref:
            self.tx_ref = f"TRX-{uuid.uuid4().hex[:12].upper()}-{int(timezone.now().timestamp())}"
        
        # Update booking status if payment is successful
        if self.status == 'success' and self.booking.status != 'confirmed':
            self.booking.status = 'confirmed'
            self.booking.save()
        
        super().save(*args, **kwargs)
    
    def mark_as_paid(self, transaction_id=None, payment_date=None):
        """Mark payment as successful"""
        self.status = 'success'
        if transaction_id:
            self.chapa_transaction_id = transaction_id
        if payment_date:
            self.payment_date = payment_date
        else:
            self.payment_date = timezone.now()
        self.save()
        
        # Update booking status
        self.booking.status = 'confirmed'
        self.booking.save()
        
        # Trigger confirmation email
        from .tasks import send_payment_confirmation_email
        send_payment_confirmation_email.delay(
            payment_id=str(self.id),
            user_email=self.customer_email
        )
    
    def mark_as_failed(self, error_message=None):
        """Mark payment as failed"""
        self.status = 'failed'
        if error_message:
            self.error_message = error_message
        self.save()