# shop/context_processors.py
from .models import CartItem

def cart_count(request):
    """Add cart count to all templates (session-based)"""
    session_key = request.session.session_key or request.session.create()
    count = CartItem.objects.filter(session_key=session_key).count()
    
    return {
        'cart_count': count,
    }
