from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Payment, Booking
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_payment_confirmation_email(payment_id, user_email):
    """Send payment confirmation email"""
    try:
        payment = Payment.objects.get(id=payment_id)
        booking = payment.booking
        
        subject = f"Payment Confirmation - Booking #{booking.id}"
        
        # Render HTML email
        html_message = render_to_string('listings/emails/payment_confirmation.html', {
            'booking': booking,
            'payment': payment,
            'user_email': user_email,
        })
        
        # Plain text version
        message = f"""
        Dear {payment.customer_first_name} {payment.customer_last_name},
        
        Your payment of {payment.amount} {payment.currency} has been confirmed.
        
        Booking Details:
        - Booking ID: {booking.id}
        - Check-in: {booking.check_in}
        - Check-out: {booking.check_out}
        - Total Paid: {payment.amount} {payment.currency}
        - Payment Method: {payment.get_payment_method_display()}
        
        Thank you for choosing our service!
        
        Best regards,
        Travel Booking Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Payment confirmation email sent to {user_email}")
        return True
        
    except Payment.DoesNotExist:
        logger.error(f"Payment with ID {payment_id} not found")
        return False
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

@shared_task
def verify_payment_status(payment_id):
    """Background task to verify payment status"""
    from .views import verify_chapa_payment
    
    try:
        payment = Payment.objects.get(id=payment_id)
        if payment.status == 'pending':
            # Call verification function
            return verify_chapa_payment(payment.tx_ref)
    except Payment.DoesNotExist:
        logger.error(f"Payment with ID {payment_id} not found")
        return False
    except Exception as e:
        logger.error(f"Payment verification failed: {str(e)}")
        return False