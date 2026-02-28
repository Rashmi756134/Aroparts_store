# shop/emails.py

from django.core.mail import send_mail
from django.conf import settings
import logging
import threading
import os

logger = logging.getLogger(__name__)


def send_order_confirmation_email_async(order, order_items):
    """
    Send order confirmation email in background (won't block the page)
    """
    def send_email_thread():
        try:
            # Check if email is configured
            email_user = os.environ.get('EMAIL_HOST_USER') or getattr(settings, 'EMAIL_HOST_USER', None)
            email_password = os.environ.get('EMAIL_HOST_PASSWORD') or getattr(settings, 'EMAIL_HOST_PASSWORD', None)
            
            logger.info(f"Email config check - USER: {email_user}, PASSWORD SET: {bool(email_password)}")
            
            if not email_user or not email_password:
                logger.error("Email not configured! Add EMAIL_HOST_USER and EMAIL_HOST_PASSWORD to settings.")
                print("EMAIL NOT CONFIGURED!")
                return
            
            # Calculate shipping
            shipping = 0 if order.total_amount >= 1500 else 99
            subtotal = order.total_amount - shipping
            
            subject = f'Order Confirmation - Aro Parts #{order.id}'
            
            message = f"""
Dear {order.customer_name},

Thank you for your order! We've received your order and it's being processed.

ORDER DETAILS
=============
Order ID: #{order.id}
Order Date: {order.created_at.strftime('%d %B %Y, %I:%M %p')}

ITEMS
-----
"""
            
            for item in order_items:
                message += f"• {item.product_name} (Qty: {item.quantity}) - ₹{item.product_price}\n"
            
            message += f"""
ORDER SUMMARY
=============
Subtotal: ₹{subtotal}
Shipping: {'FREE' if shipping == 0 else f'₹{shipping}'}
Total: ₹{order.total_amount}

SHIPPING ADDRESS
================
{order.customer_name}
{order.shipping_address}
{order.city}, {order.state} - {order.zip_code}
Phone: {order.customer_phone}

PAYMENT STATUS: PAID

Thank you for shopping with Aro Parts!

Best regards,
Aro Parts Team
            """
            
            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.customer_email],
                fail_silently=False,
            )
            
            logger.info(f"✅ Email sent successfully to {order.customer_email} for order #{order.id}")
            print(f"✅ EMAIL SENT to {order.customer_email}")
            
        except Exception as e:
            logger.error(f"❌ Email error: {e}")
            print(f"❌ EMAIL ERROR: {e}")
    
    # Start in background
    email_thread = threading.Thread(target=send_email_thread)
    email_thread.start()


def send_order_confirmation_email(order, order_items):
    """Wrapper function"""
    send_order_confirmation_email_async(order, order_items)
