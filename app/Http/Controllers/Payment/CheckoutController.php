<?php

namespace App\Http\Controllers\Payment;

use App\Http\Controllers\Controller;
use App\Models\Payment;
use App\Services\PaymentService;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;

class CheckoutController extends Controller
{
    public function __construct(
        private PaymentService $paymentService,
    ) {
    }

    public function show(string $checkoutId): View
    {
        $amount = session('checkout_amount', 0.00);
        $description = session('checkout_description', 'Payment');

        return view('payment.checkout', [
            'checkoutId' => $checkoutId,
            'amount' => $amount,
            'description' => $description,
        ]);
    }

    public function process(Request $request, string $checkoutId): RedirectResponse
    {
        $validated = $request->validate([
            'card_number' => ['required', 'string'],
            'card_name' => ['required', 'string', 'max:255'],
            'expiry_month' => ['required', 'string', 'size:2'],
            'expiry_year' => ['required', 'string', 'min:2', 'max:4'],
            'cvv' => ['required', 'string', 'min:3', 'max:4'],
        ]);

        $result = $this->paymentService->processPayment(
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
            $payment = Payment::find($paymentId);
            if ($payment) {
                $this->paymentService->completePayment($payment, $result['transaction_id'] ?? null);
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
