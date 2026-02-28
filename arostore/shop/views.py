from urllib import request
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Product, Category, CartItem, Order, OrderItem
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CartItem, Order, OrderItem
from .emails import send_order_confirmation_email_async

# Setup logging
logger = logging.getLogger(__name__)

# Free shipping settings
FREE_SHIPPING_THRESHOLD = 1500
SHIPPING_CHARGE = 99


# ==================== PRODUCT VIEWS ====================

def product_list(request):
    """Display all available products"""
    products = Product.objects.filter(in_stock=True)
    categories = Category.objects.all()
    
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category')
    
    if search_query:
        products = products.filter(name__icontains=search_query)
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    context = {
        'products': products,
        'categories': categories,
        'current_category': category_id,
        'search_query': search_query,
    }
    return render(request, 'shop/product_list.html', context)


def product_detail(request, product_id):
    """Display single product details"""
    product = get_object_or_404(Product, id=product_id, in_stock=True)
    return render(request, 'shop/product_detail.html', {'product': product})


# ==================== CART VIEWS ====================

def cart_count(request):
    """Get cart item count for AJAX requests"""
    session_key = request.session.session_key or request.session.create()
    count = CartItem.objects.filter(session_key=session_key).count()
    return JsonResponse({'count': count})


def cart_view(request):
    """Display the shopping cart"""
    session_key = request.session.session_key or request.session.create()
    cart_items = CartItem.objects.filter(session_key=session_key)
    
    subtotal = sum(item.total_price for item in cart_items)
    
    # Free shipping logic
    if subtotal >= FREE_SHIPPING_THRESHOLD:
        shipping = 0
        free_shipping_message = True
    else:
        shipping = SHIPPING_CHARGE if cart_items else 0
        free_shipping_message = False
    
    remaining_for_free = FREE_SHIPPING_THRESHOLD - subtotal
    total = subtotal + shipping
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
        'free_shipping_threshold': FREE_SHIPPING_THRESHOLD,
        'free_shipping_message': free_shipping_message,
        'remaining_for_free': remaining_for_free if remaining_for_free > 0 else 0,
    }
    return render(request, 'shop/cart.html', context)


def add_to_cart(request):
    """Add product to cart via AJAX"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        
        product = get_object_or_404(Product, id=product_id)
        session_key = request.session.session_key or request.session.create()
        
        cart_item, created = CartItem.objects.get_or_create(
            session_key=session_key,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        cart_count = CartItem.objects.filter(session_key=session_key).count()
        
        return JsonResponse({
            'success': True,
            'message': f'{product.name} added to cart!',
            'cart_count': cart_count
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


def update_cart(request):
    """Update quantity of cart item"""
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))
        
        session_key = request.session.session_key or request.session.create()
        cart_item = get_object_or_404(CartItem, id=item_id, session_key=session_key)
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})


def remove_from_cart(request):
    """Remove item from cart"""
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        
        session_key = request.session.session_key or request.session.create()
        cart_item = get_object_or_404(CartItem, id=item_id, session_key=session_key)
        cart_item.delete()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})


# ==================== CHECKOUT & PAYMENT VIEWS ====================

@login_required(login_url='/accounts/login/')
def checkout(request):
    """Display checkout page"""
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
        
    cart_items = CartItem.objects.filter(session_key=request.session.session_key)
    
    if not cart_items:
        messages.error(request, 'Your cart is empty')
        return redirect('product_list')
    
    subtotal = sum(item.total_price for item in cart_items)
    
    # Free shipping logic
    if subtotal >= FREE_SHIPPING_THRESHOLD:
        shipping = 0
        free_shipping_message = True
    else:
        shipping = SHIPPING_CHARGE
        free_shipping_message = False
    
    remaining_for_free = FREE_SHIPPING_THRESHOLD - subtotal
    total = subtotal + shipping
        
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
        'free_shipping_threshold': FREE_SHIPPING_THRESHOLD,
        'free_shipping_message': free_shipping_message,
        'remaining_for_free': remaining_for_free if remaining_for_free > 0 else 0,
    }
    return render(request, 'shop/checkout.html', context)


# ==================== PAYMENT PROCESSING VIEWS ====================

@login_required(login_url='/accounts/login/')
def process_payment(request):
    """Process payment with razorpay"""
    
    if request.method == 'POST':
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        cart_items = CartItem.objects.filter(session_key=session_key)
        
        if not cart_items:
            return JsonResponse({'success': False, 'error': 'Cart is empty'})
        
        subtotal = sum(item.total_price for item in cart_items)
        
        # Free shipping logic
        if subtotal >= FREE_SHIPPING_THRESHOLD:
            shipping = 0
        else:
            shipping = SHIPPING_CHARGE
        
        total = subtotal + shipping
        
        customer_name = request.POST.get('name')
        customer_email = request.POST.get('email')
        customer_phone = request.POST.get('phone')
        shipping_address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')
        landmark = request.POST.get('landmark', '')
        
        # Create order with all fields
        order = Order.objects.create(
            user=request.user,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            shipping_address=shipping_address,
            city=city,
            state=state,
            zip_code=zip_code,
            landmark=landmark,
            total_amount=total,
            payment_method='razorpay',
            payment_status='pending',
            status='processing'
        )
            
        # Create order items
        for item in cart_items:
            product_image_url = ''
            if item.product.image:
                product_image_url = item.product.image.url
                    
            OrderItem.objects.create(
                order=order,
                product_name=item.product.name,
                product_price=item.product.price,
                quantity=item.quantity,
                product_image=product_image_url
            )
            
        # Clear cart
        cart_items.delete()
        
        from .razorpay import create_order
        
        try:
            razorpay_order = create_order(total, order.id)
            
            context = {
                'order': order,
                'razorpay_key': settings.RAZORPAY_KEY_ID,
                'razorpay_order_id': razorpay_order['id'],
                'amount': int(total * 100),
                'customer_name': customer_name,
                'customer_email': customer_email,
                'customer_phone': customer_phone,
            }
            
            return render(request, 'shop/razorpay_checkout.html', context)
        
        except Exception as e:
            # If Razorpay fails, cancel order
            order.payment_status = 'failed'
            order.status = 'cancelled'
            order.save()
            
            messages.error(request, f"Payment error: {str(e)}")
            return redirect('checkout')
    
    return redirect('checkout')


# ==================== PAYMENT SUCCESS & HISTORY VIEWS ====================

@login_required(login_url='/accounts/login/')
def payment_success(request, order_id):
    """Handle successful payment"""
    print("=" * 50)
    print("PAYMENT SUCCESS VIEW CALLED")
    print("=" * 50)
    
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        print(f"Order found: {order.id}")
        
        # Update order status
        order.payment_status = 'paid'
        order.save()
        print("Order marked as paid")
        
        # Get order items
        order_items = OrderItem.objects.filter(order=order)
        
        # Send confirmation email - USE ASYNC VERSION
        print("Calling email function...")
        send_order_confirmation_email_async(order, order_items)
        print("Email function called")
        
        context = {
            'order': order,
            'order_items': order_items,
        }
        
        return render(request, 'shop/payment_success.html', context)
        
    except Order.DoesNotExist:
        print("Order not found")
        messages.error(request, 'Order not found')
        return redirect('product_list')
    except Exception as e:
        print(f"Error in payment success: {str(e)}")
        logger.error(f"Payment success error: {e}")
        messages.error(request, 'Error processing payment')
        return redirect('product_list')


# Handle payment cancellation
def payment_cancel(request, order_id):
    """Handle cancelled payment"""
    try:
        order = Order.objects.get(id=order_id)
        order.payment_status = 'cancelled'
        order.status = 'cancelled'
        order.save()
        
        messages.warning(request, 'Payment was cancelled')
    except Order.DoesNotExist:
        pass
    
    return redirect('checkout')


@login_required(login_url='/accounts/login/')
def order_history(request):
    """Order history page"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    
    return render(request, 'shop/order_history.html', context)


@login_required(login_url='/accounts/login/')
def order_detail(request, order_id):
    """Order detail page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    
    # Calculate shipping
    if order.total_amount >= 1500:
        shipping = 0
    else:
        shipping = 99
    
    # Calculate subtotal (total - shipping)
    subtotal = order.total_amount - shipping
    
    context = {
        'order': order,
        'order_items': order_items,
        'subtotal': subtotal,
        'shipping': shipping,
    }
    
    return render(request, 'shop/order_detail.html', context)


# ==================== TEST EMAIL VIEW ====================

def test_email(request):
    """Test email function"""
    print("=" * 50)
    print("TEST EMAIL VIEW CALLED")
    print("=" * 50)
    
    try:
        from django.core.mail import send_mail
        
        print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        
        send_mail(
            'Test Email from Aro Parts',
            'This is a test email from Render deployment!',
            settings.DEFAULT_FROM_EMAIL,
            [settings.DEFAULT_FROM_EMAIL],
            fail_silently=False,
        )
        
        print("Test email sent successfully!")
        return JsonResponse({'success': True, 'message': 'Email sent!'})
        
    except Exception as e:
        print(f"Test email failed: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})
