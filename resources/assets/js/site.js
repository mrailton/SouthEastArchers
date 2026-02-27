import Alpine from '@alpinejs/csp'
import '../css/site.css'

// === Public site & member area Alpine components ===

// Navigation mobile menu
Alpine.data('mobileNav', () => ({
    open: false,
    toggle() {
        this.open = !this.open
    }
}))

// Payment form with double-click prevention
Alpine.data('paymentForm', () => ({
    isSubmitting: false,
    handleSubmit(event) {
        if (this.isSubmitting) {
            event.preventDefault()
            return false
        }
        this.isSubmitting = true
        return true
    }
}))

// Credit payment form with quantity selection
Alpine.data('creditPaymentForm', () => ({
    quantity: '1',
    isSubmitting: false,
    handleSubmit(event) {
        if (this.isSubmitting) {
            event.preventDefault()
            return false
        }
        this.isSubmitting = true
        return true
    }
}))

// Initialize Alpine.js
window.Alpine = Alpine
Alpine.start()

// Card number formatting (for checkout page)
document.addEventListener('DOMContentLoaded', () => {
    const cardInput = document.querySelector('input[name="card_number"]')
    if (cardInput) {
        cardInput.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\s/g, '')
            let formattedValue = value.match(/.{1,4}/g)?.join(' ') || value
            e.target.value = formattedValue
        })
    }
})

