<?php

namespace App\Http\Controllers\Payment;

use App\Http\Controllers\Controller;
use App\Services\PaymentService;
use App\Settings\ApplicationSettings;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;

class CreditPurchaseController extends Controller
{
    public function __construct(
        private PaymentService $paymentService,
        private ApplicationSettings $settings,
    ) {
    }

    public function show(): View
    {
        return view('payment.credits', [
            'creditCost' => $this->settings->additional_shoot_cost / 100.0,
        ]);
    }

    public function store(Request $request): RedirectResponse
    {
        $validated = $request->validate([
            'quantity' => ['required', 'integer', 'min:1', 'max:100'],
            'payment_method' => ['nullable', 'string', 'in:online,cash'],
        ]);

        $quantity = (int) $validated['quantity'];
        $paymentMethod = $validated['payment_method'] ?? 'online';

        /** @var \App\Models\User $user */
        $user = $request->user();

        if ($paymentMethod === 'cash') {
            $payment = $this->paymentService->createCashCreditPayment($user, $quantity);

            return redirect()->route('credits')
                ->with('success', 'Cash payment registered. An admin will confirm your payment shortly.');
        }

        $result = $this->paymentService->initiateCreditPurchase($user, $quantity);

        if ($result['success']) {
            // Store payment info in session for checkout
            session([
                'credit_payment_id' => $result['payment_id'],
                'credit_quantity' => $result['quantity'],
                'checkout_amount' => $result['amount'],
                'checkout_description' => $result['description'],
            ]);

            return redirect()->route('payment.checkout', ['checkout_id' => $result['checkout_id']]);
        }

        return back()->with('error', $result['error'] ?? 'Error creating payment.');
    }
}
