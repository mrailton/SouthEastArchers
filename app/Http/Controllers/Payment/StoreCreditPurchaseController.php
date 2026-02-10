<?php

namespace App\Http\Controllers\Payment;

use App\Http\Controllers\Controller;
use App\Models\User;
use App\Services\PaymentService;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;

class StoreCreditPurchaseController extends Controller
{
    /**
     * Process the credit purchase.
     */
    public function __invoke(Request $request, PaymentService $paymentService): RedirectResponse
    {
        $validated = $request->validate([
            'quantity' => ['required', 'integer', 'min:1', 'max:100'],
            'payment_method' => ['nullable', 'string', 'in:online,cash'],
        ]);

        $quantity = (int) $validated['quantity'];
        $paymentMethod = $validated['payment_method'] ?? 'online';

        /** @var User $user */
        $user = $request->user();

        if ($paymentMethod === 'cash') {
            $paymentService->createCashCreditPayment($user, $quantity);

            return redirect()->route('credits')
                ->with('success', 'Cash payment registered. An admin will confirm your payment shortly.');
        }

        $result = $paymentService->initiateCreditPurchase($user, $quantity);

        if ($result['success']) {
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
