import Alpine from '@alpinejs/csp'
import '../css/style.css'

// Register Alpine.js components for CSP compliance
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

// Payment actions for pending payments page
Alpine.data('paymentActions', () => ({
    showModal: false,
    modalType: 'success',
    modalTitle: '',
    modalMessage: '',
    confirmText: '',
    formAction: '',
    
    showApproveModal(paymentId, memberName, paymentType) {
        this.modalType = 'success'
        this.modalTitle = 'Approve Payment'
        this.modalMessage = `Approve ${paymentType} payment for ${memberName}? This will activate their membership or add credits to their account.`
        this.confirmText = 'Approve'
        this.formAction = `/admin/payments/${paymentId}/approve`
        this.showModal = true
    },
    
    showRejectModal(paymentId, memberName) {
        this.modalType = 'danger'
        this.modalTitle = 'Reject Payment'
        this.modalMessage = `Reject payment for ${memberName}? This action cannot be undone.`
        this.confirmText = 'Reject'
        this.formAction = `/admin/payments/${paymentId}/reject`
        this.showModal = true
    }
}))

// Dashboard actions
Alpine.data('dashboardActions', () => ({
    showModal: false,
    modalTitle: '',
    modalMessage: '',
    formAction: '',
    
    showApproveModal(paymentId, memberName, paymentType) {
        this.modalTitle = 'Approve Payment'
        this.modalMessage = `Approve ${paymentType} payment for ${memberName}? This will activate their membership or add credits to their account.`
        this.formAction = `/admin/payments/${paymentId}/approve`
        this.showModal = true
    }
}))

// Member detail actions
Alpine.data('memberDetailActions', () => ({
    showActivateModal: false,
    showConfirmModal: false,
    showCreditsModal: false,
    modalType: 'success',
    modalTitle: '',
    modalMessage: '',
    confirmText: '',
    formAction: '',
    // add-credits modal state
    creditsQuantity: 1,
    creditsReason: '',
    creditsAction: '',

    showAddCreditsModal(actionUrl) {
        this.creditsAction = actionUrl
        this.showCreditsModal = true
    },

    showMembershipModal(action, actionUrl) {
        if (action === 'activate') {
            this.modalType = 'success'
            this.modalTitle = 'Activate Membership'
            this.modalMessage = 'Are you sure you want to activate this membership?'
            this.confirmText = 'Activate'
        } else if (action === 'renew') {
            this.modalType = 'success'
            this.modalTitle = 'Renew Membership'
            this.modalMessage = 'Are you sure you want to renew this membership? This will reset their credits and extend their expiry date.'
            this.confirmText = 'Renew'
        }
        this.formAction = actionUrl
        this.showConfirmModal = true
    },
    
    showPaymentModal(action, paymentId, paymentType) {
        if (action === 'approve') {
            this.modalType = 'success'
            this.modalTitle = 'Approve Payment'
            this.modalMessage = `Approve this ${paymentType} payment? This will activate their membership or add credits to their account.`
            this.confirmText = 'Approve'
            this.formAction = `/admin/payments/${paymentId}/approve`
        } else if (action === 'reject') {
            this.modalType = 'danger'
            this.modalTitle = 'Reject Payment'
            this.modalMessage = 'Reject this payment? This action cannot be undone.'
            this.confirmText = 'Reject'
            this.formAction = `/admin/payments/${paymentId}/reject`
        }
        this.showConfirmModal = true
    }
}))

// Roles management actions
Alpine.data('rolesActions', () => ({
    showModal: false,
    roleName: '',
    formAction: '',
    
    showDeleteModal(roleId, roleName) {
        this.roleName = roleName
        this.formAction = `/admin/roles/${roleId}/delete`
        this.showModal = true
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
