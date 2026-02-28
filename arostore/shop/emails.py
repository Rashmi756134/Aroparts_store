# shop/emails.py

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)


def send_order_confirmation_email(order, order_items):
    """
    Send order confirmation email to customer
    
    Args:
        order: Order object
        order_items: QuerySet of OrderItem objects
    """
    try:
        customer_email = order.customer_email
        customer_name = order.customer_name
        
        # Email subject
        subject = f'Order Confirmation - Aro Parts #{order.id}'
        
        # Plain text message
        message = f"""
Dear {customer_name},

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
Subtotal: ₹{order.total_amount - 50}
Shipping: {'FREE' if order.total_amount >= 1500 else '₹50'}
Total: ₹{order.total_amount}

SHIPPING ADDRESS
================
{order.customer_name}
{order.shipping_address}
{order.city}, {order.state} - {order.zip_code}
Phone: {order.customer_phone}

PAYMENT METHOD
==============
Razorpay Payment {'(Paid)' if order.payment_status == 'paid' else '(Pending)'}

WHAT'S NEXT?
============
We'll send you another email once your order is shipped.

Thank you for shopping with Aro Parts!

Best regards,
Aro Parts Team
        """
        
        # HTML message (optional)
        html_message = render_to_string('shop/emails/order_confirmation.html', {
            'order': order,
            'order_items': order_items,
        })
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[customer_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Order confirmation email sent to {customer_email} for order #{order.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send order confirmation email: {e}")
        return False


def send_order_shipped_email(order):
    """
    Send order shipped notification email
    """
    try:
        subject = f'Order Shipped - Aro Parts #{order.id}'
        
        message = f"""
Dear {order.customer_name},

Great news! Your order has been shipped.

ORDER DETAILS
=============
Order ID: #{order.id}
Tracking: {order.tracking_number if hasattr(order, 'tracking_number') else 'N/A'}

Thank you for shopping with Aro Parts!

Best regards,
Aro Parts Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.customer_email],
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send shipped email: {e}")
        return False