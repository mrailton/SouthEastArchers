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
            $redirectUrl = $request->input('redirect', route('admin.payments.pending'));

            return redirect($redirectUrl)
                ->with('error', 'Payment is not pending.');
        }

        $paymentService->completePayment($payment, 'cash_confirmed');

        // Redirect back to the referring page if specified, otherwise to pending payments
        $redirectUrl = $request->input('redirect', route('admin.payments.pending'));

        return redirect($redirectUrl)
            ->with('success', 'Payment confirmed successfully.');
    }
}
