// Cart functionality
let cart = [];

/**
 * Add product to cart
 */
function addToCart(productId, productName) {
    fetch('/cart/add/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: `product_id=${productId}&quantity=1`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message);
            updateCartBadge(data.cart_count);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error adding product to cart');
    });
}

/**
 * Add product to cart with quantity
 */
function addToCartWithQuantity(productId, quantity) {
    fetch('/cart/add/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: `product_id=${productId}&quantity=${quantity}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message);
            updateCartBadge(data.cart_count);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error adding product to cart');
    });
}

/**
 * Update cart badge in navbar
 */
function updateCartBadge(count) {
    const badge = document.getElementById('cart-count-badge');
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'flex' : 'none';
    }
}

/**
 * Update cart item quantity
 */
function updateQuantity(itemId, newQuantity) {
    if (newQuantity < 1) {
        removeItem(itemId);
        return;
    }
    
    fetch('/cart/update/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: `item_id=${itemId}&quantity=${newQuantity}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error updating quantity');
    });
}

/**
 * Remove item from cart
 */
function removeItem(itemId) {
    if (confirm('Are you sure you want to remove this item?')) {
        fetch('/cart/remove/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: `item_id=${itemId}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error removing item');
        });
    }
}

/**
 * Show notification toast
 */
function showNotification(message) {
    // Remove existing notifications
    const existing = document.querySelector('.toast-notification');
    if (existing) {
        existing.remove();
    }
    
    const notification = document.createElement('div');
    notification.className = 'toast-notification';
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #008060;
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease;
        font-family: -apple-system, BlinkMacSystemFont, "San Francisco", "Segoe UI", Roboto, sans-serif;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 10px;
    `;
    
    // Add checkmark icon
    notification.innerHTML = `
        <svg viewBox="0 0 20 20" style="width: 20px; height: 20px; fill: white;">
            <path d="M10 20a10 10 0 1 1 0-20 10 10 0 0 1 0 20zm-2-8l-3-3-1.5 1.5 4.5 4.5 9-9-1.5-1.5L8 12z"/>
        </svg>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (notification.parentElement) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

/**
 * Show error notification
 */
function showErrorNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #d82c0d;
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 10px;
    `;
    
    notification.innerHTML = `
        <svg viewBox="0 0 20 20" style="width: 20px; height: 20px; fill: white;">
            <path d="M10 20a10 10 0 1 1 0-20 10 10 0 0 1 0 20zm1-5h2a1 1 0 0 0 0-2H9v-2a1 1 0 0 0-2 0v4H5a1 1 0 0 0 0 2h2v3a1 1 0 0 0 2 0v-3h2a1 1 0 0 0 0-2h-2z"/>
        </svg>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (notification.parentElement) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

/**
 * Get CSRF token from cookies
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Format price to currency
 */
function formatPrice(price) {
    return '$' + parseFloat(price).toFixed(2);
}

/**
 * Change main product image (for product detail page)
 */
function changeImage(imageUrl, thumbnail) {
    // Change main image source
    const mainImage = document.getElementById('main-image');
    if (mainImage) {
        mainImage.src = imageUrl;
    }
    
    // Update thumbnail borders
    const thumbnails = document.querySelectorAll('.thumbnail-image');
    thumbnails.forEach(thumb => {
        thumb.style.border = '2px solid transparent';
    });
    if (thumbnail) {
        thumbnail.style.border = '2px solid #008060';
    }
}

/**
 * Initialize on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Aro Parts Store loaded successfully!');
    
    // Add CSS animations
    addAnimationStyles();
});

/**
 * Add animation CSS styles dynamically
 */
function addAnimationStyles() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
    `;
    document.head.appendChild(style);
}