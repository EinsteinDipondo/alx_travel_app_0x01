from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import Booking, Payment, Listing
from .serializers import BookingSerializer, PaymentSerializer, PaymentInitiateSerializer
import requests
import json
import logging
from .tasks import verify_payment_status
from django.utils import timezone

logger = logging.getLogger(__name__)

class PaymentViewSet(viewsets.ModelViewSet):
    """Handle payment operations"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return payments for the authenticated user"""
        return Payment.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'], url_path='initiate')
    def initiate_payment(self, request):
        """Initiate payment with Chapa API"""
        serializer = PaymentInitiateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get booking
            booking_id = serializer.validated_data['booking_id']
            booking = get_object_or_404(Booking, id=booking_id, user=request.user)
            
            # Create payment record
            payment = Payment.objects.create(
                booking=booking,
                user=request.user,
                amount=booking.total_price,
                currency='ETB',
                customer_email=request.user.email,
                customer_first_name=request.user.first_name or 'Customer',
                customer_last_name=request.user.last_name or 'User',
                customer_phone=serializer.validated_data.get('phone_number'),
                description=f"Payment for booking #{booking.id}",
                metadata={
                    'booking_id': str(booking.id),
                    'user_id': str(request.user.id),
                }
            )
            
            # Prepare Chapa API request
            headers = {
                'Authorization': f'Bearer {settings.CHAPA_SECRET_KEY}',
                'Content-Type': 'application/json',
            }
            
            payload = {
                'amount': str(payment.amount),
                'currency': payment.currency,
                'email': payment.customer_email,
                'first_name': payment.customer_first_name,
                'last_name': payment.customer_last_name,
                'tx_ref': payment.tx_ref,
                'callback_url': f"{settings.CHAPA_WEBHOOK_URL}?tx_ref={payment.tx_ref}",
                'return_url': serializer.validated_data.get('return_url', ''),
                'customization': {
                    'title': 'Travel Booking Payment',
                    'description': payment.description,
                }
            }
            
            if payment.customer_phone:
                payload['phone_number'] = payment.customer_phone
            
            # Make API call to Chapa
            try:
                response = requests.post(
                    settings.CHAPA_API_URL,
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=30
                )
                
                response_data = response.json()
                
                if response.status_code == 200 and response_data.get('status') == 'success':
                    # Update payment with checkout URL
                    payment.checkout_url = response_data['data']['checkout_url']
                    payment.chapa_transaction_id = response_data['data'].get('transaction_id')
                    payment.save()
                    
                    return Response({
                        'success': True,
                        'message': 'Payment initiated successfully',
                        'payment_id': str(payment.id),
                        'tx_ref': payment.tx_ref,
                        'checkout_url': payment.checkout_url,
                        'amount': payment.amount,
                        'currency': payment.currency,
                    }, status=status.HTTP_200_OK)
                else:
                    error_msg = response_data.get('message', 'Payment initiation failed')
                    payment.status = 'failed'
                    payment.error_message = error_msg
                    payment.save()
                    
                    return Response({
                        'success': False,
                        'message': error_msg,
                        'details': response_data
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Chapa API request failed: {str(e)}")
                payment.status = 'failed'
                payment.error_message = str(e)
                payment.save()
                
                return Response({
                    'success': False,
                    'message': 'Failed to connect to payment gateway',
                    'error': str(e)
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
        except Exception as e:
            logger.error(f"Payment initiation error: {str(e)}")
            return Response({
                'success': False,
                'message': 'Internal server error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='verify/(?P<tx_ref>[^/.]+)')
    def verify_payment(self, request, tx_ref=None):
        """Verify payment status with Chapa API"""
        try:
            # Get payment
            payment = get_object_or_404(Payment, tx_ref=tx_ref, user=request.user)
            
            # Verify with Chapa API
            headers = {
                'Authorization': f'Bearer {settings.CHAPA_SECRET_KEY}',
            }
            
            response = requests.get(
                f"{settings.CHAPA_VERIFY_URL}{tx_ref}",
                headers=headers,
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status') == 'success':
                transaction_data = response_data['data']
                
                # Update payment status
                if transaction_data['status'] == 'success':
                    payment.mark_as_paid(
                        transaction_id=transaction_data.get('id'),
                        payment_date=timezone.now()
                    )
                    
                    return Response({
                        'success': True,
                        'message': 'Payment verified successfully',
                        'status': 'success',
                        'payment': PaymentSerializer(payment).data,
                        'booking': BookingSerializer(payment.booking).data
                    }, status=status.HTTP_200_OK)
                    
                elif transaction_data['status'] == 'failed':
                    payment.mark_as_failed('Payment failed at gateway')
                    
                    return Response({
                        'success': False,
                        'message': 'Payment failed',
                        'status': 'failed',
                        'payment': PaymentSerializer(payment).data
                    }, status=status.HTTP_200_OK)
                    
            else:
                error_msg = response_data.get('message', 'Verification failed')
                return Response({
                    'success': False,
                    'message': error_msg,
                    'details': response_data
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Payment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Payment verification error: {str(e)}")
            return Response({
                'success': False,
                'message': 'Internal server error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='webhook', permission_classes=[])
    def payment_webhook(self, request):
        """Handle Chapa payment webhook"""
        try:
            # Verify webhook signature (implement based on Chapa documentation)
            event_data = request.data
            
            tx_ref = event_data.get('tx_ref')
            status = event_data.get('status')
            transaction_id = event_data.get('id')
            
            if not tx_ref:
                return Response({'error': 'Missing tx_ref'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                payment = Payment.objects.get(tx_ref=tx_ref)
                
                if status == 'success':
                    payment.mark_as_paid(
                        transaction_id=transaction_id,
                        payment_date=timezone.now()
                    )
                elif status == 'failed':
                    payment.mark_as_failed('Payment failed via webhook')
                
                # Schedule verification task for additional safety
                verify_payment_status.delay(str(payment.id))
                
                return Response({'success': True}, status=status.HTTP_200_OK)
                
            except Payment.DoesNotExist:
                logger.error(f"Payment with tx_ref {tx_ref} not found")
                return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def verify_chapa_payment(tx_ref):
    """Utility function to verify payment (can be called from tasks)"""
    try:
        payment = Payment.objects.get(tx_ref=tx_ref)
        
        headers = {
            'Authorization': f'Bearer {settings.CHAPA_SECRET_KEY}',
        }
        
        response = requests.get(
            f"{settings.CHAPA_VERIFY_URL}{tx_ref}",
            headers=headers,
            timeout=30
        )
        
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get('status') == 'success':
            transaction_data = response_data['data']
            
            if transaction_data['status'] == 'success' and payment.status != 'success':
                payment.mark_as_paid(
                    transaction_id=transaction_data.get('id'),
                    payment_date=timezone.now()
                )
                return True
            elif transaction_data['status'] == 'failed' and payment.status == 'pending':
                payment.mark_as_failed('Payment verification failed')
                return False
        
        return False
        
    except Exception as e:
        logger.error(f"Payment verification failed for {tx_ref}: {str(e)}")
        return False