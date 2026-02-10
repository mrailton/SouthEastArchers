<?php

namespace App\Http\Controllers\Payment;

use App\Http\Controllers\Controller;
use App\Services\PaymentService;
use App\Settings\ApplicationSettings;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;

class MembershipPaymentController extends Controller
{
    public function __construct(
        private PaymentService $paymentService,
        private ApplicationSettings $settings,
    ) {
    }

    public function show(): View
    {
        return view('payment.membership', [
            'annualCost' => $this->settings->annual_membership_cost / 100.0,
            'shootsIncluded' => $this->settings->membership_shoots_included,
        ]);
    }

    public function store(Request $request): RedirectResponse
    {
        $paymentMethod = $request->input('payment_method', 'online');

        /** @var \App\Models\User $user */
        $user = $request->user();

        if ($paymentMethod === 'cash') {
            $payment = $this->paymentService->createCashMembershipPayment($user);

            return redirect()->route('dashboard')
                ->with('success', 'Cash payment registered. An admin will confirm your payment shortly.');
        }

        $result = $this->paymentService->initiateMembershipPayment($user);

        if ($result['success']) {
            // Store payment info in session for checkout
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
