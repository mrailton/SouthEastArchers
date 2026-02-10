<?php

namespace App\Http\Controllers\Admin\Payments;

use App\Enums\PaymentStatus;
use App\Http\Controllers\Controller;
use App\Models\Payment;
use App\Services\PaymentService;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;

class ConfirmCashPaymentController extends Controller
{
    /**
     * Confirm a pending cash payment.
     */
    public function __invoke(Request $request, Payment $payment, PaymentService $paymentService): RedirectResponse
    {
        if ($payment->status !== PaymentStatus::Pending) {
            return redirect()->route('admin.payments.pending')
                ->with('error', 'Payment is not pending.');
        }

        $paymentService->completePayment($payment, 'cash_confirmed');

        return redirect()->route('admin.payments.pending')
            ->with('success', 'Payment confirmed successfully.');
    }
}
