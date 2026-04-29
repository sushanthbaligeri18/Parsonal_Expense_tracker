/* ============================================================================
   MAIN JAVASCRIPT
   ============================================================================ */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips or other global functionality here
    console.log('CarShare application loaded');
});

// Close alert messages
function closeAlert(element) {
    element.style.display = 'none';
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Format date
function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}
