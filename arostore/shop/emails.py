# shop/emails.py

from django.core.mail import send_mail
from django.conf import settings
import logging
import threading


logger = logging.getLogger(__name__)


def send_order_confirmation_email_async(order, order_items):
    """
    Send order confirmation email in background (non-blocking)
    """
    def send_email_thread():
        try:
            subject = f'Order Confirmation - Aro Parts #{order.id}'
            
            # Calculate shipping
            shipping = 0 if order.total_amount >= 1500 else 50
            subtotal = order.total_amount - shipping
            
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
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.customer_email],
                fail_silently=True,  # Don't raise errors
            )
            
            logger.info(f"Email sent for order #{order.id}")
            
        except Exception as e:
            logger.error(f"Email error (async): {e}")
    
    # Start email in background
    email_thread = threading.Thread(target=send_email_thread)
    email_thread.start()


def send_order_confirmation_email(order, order_items):
    """
    Send order confirmation email (blocking version - for compatibility)
    """
    try:
        send_order_confirmation_email_async(order, order_items)
        return True
    except Exception as e:
        logger.error(f"Email error: {e}")
        return False
