# shop/razorpay.py

import razorpay
from django.conf import settings

client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

def create_order(total_amount, order_id):
    """Create Razorpay order in INR"""
    amount_paise = int(total_amount * 100)  # Razorpay uses paise
    
    data = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": f"order_{order_id}",
        "notes": {
            "order_id": str(order_id)
        }
    }
    
    order = client.order.create(data=data)
    return order

def verify_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    """Verify Razorpay payment signature"""
    try:
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        # Verify signature
        client.utility.verify_razorpay_signature(params_dict, "")
        return True
    except:
        return False