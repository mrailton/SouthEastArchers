<?php

namespace App\Http\Controllers\Payment;

use App\Http\Controllers\Controller;
use App\Models\Payment;
use App\Services\PaymentService;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;

class ProcessCheckoutController extends Controller
{
    /**
     * Process the checkout payment.
     */
    public function __invoke(Request $request, string $checkoutId, PaymentService $paymentService): RedirectResponse
    {
        $validated = $request->validate([
            'card_number' => ['required', 'string'],
            'card_name' => ['required', 'string', 'max:255'],
            'expiry_month' => ['required', 'string', 'size:2'],
            'expiry_year' => ['required', 'string', 'min:2', 'max:4'],
            'cvv' => ['required', 'string', 'min:3', 'max:4'],
        ]);

        $result = $paymentService->processPayment(
            $checkoutId,
            $validated['card_number'],
            $validated['card_name'],
            $validated['expiry_month'],
            $validated['expiry_year'],
            $validated['cvv'],
        );

        if (! $result['success']) {
            return redirect()->route('payment.checkout', ['checkout_id' => $checkoutId])
                ->with('error', $result['error'] ?? 'Payment was not approved. Please try again.');
        }

        // Find and complete the payment
        $paymentId = session('membership_payment_id') ?? session('credit_payment_id');

        if ($paymentId) {
            /** @var Payment|null $payment */
            $payment = Payment::find($paymentId);
            if ($payment instanceof Payment) {
                /** @var string|null $transactionId */
                $transactionId = $result['transaction_id'] ?? null;
                $paymentService->completePayment($payment, $transactionId);
            }
        }

        // Clear session data
        session()->forget([
            'membership_payment_id',
            'credit_payment_id',
            'credit_quantity',
            'checkout_amount',
            'checkout_description',
        ]);

        return redirect()->route('dashboard')
            ->with('success', 'Payment processed successfully!');
    }
}
