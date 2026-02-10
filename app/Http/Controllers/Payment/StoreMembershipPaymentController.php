<?php

namespace App\Http\Controllers\Payment;

use App\Http\Controllers\Controller;
use App\Models\User;
use App\Services\PaymentService;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;

class StoreMembershipPaymentController extends Controller
{
    /**
     * Process the membership payment.
     */
    public function __invoke(Request $request, PaymentService $paymentService): RedirectResponse
    {
        $paymentMethod = $request->input('payment_method', 'online');

        /** @var User $user */
        $user = $request->user();

        if ($paymentMethod === 'cash') {
            $paymentService->createCashMembershipPayment($user);

            return redirect()->route('dashboard')
                ->with('success', 'Cash payment registered. An admin will confirm your payment shortly.');
        }

        $result = $paymentService->initiateMembershipPayment($user);

        if ($result['success']) {
            session([
                'membership_payment_id' => $result['payment_id'],
                'checkout_amount' => $result['amount'],
                'checkout_description' => $result['description'],
            ]);

            return redirect()->route('payment.checkout', ['checkout_id' => $result['checkout_id']]);
        }

        return back()->with('error', $result['error'] ?? 'Error creating payment.');
    }
}
