<?php

namespace App\Http\Controllers\Admin\Payments;

use App\Enums\PaymentStatus;
use App\Http\Controllers\Controller;
use App\Models\Payment;
use App\Services\PaymentService;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;

class ConfirmPaymentController extends Controller
{
    /**
     * Confirm a pending cash payment.
     */
    public function __invoke(Request $request, Payment $payment, PaymentService $paymentService): RedirectResponse
    {
        $redirectUrl = $request->input('redirect', route('admin.payments.pending'));

        if ($payment->status !== PaymentStatus::Pending) {
            return redirect()->to($redirectUrl)
                ->with('error', 'Payment is not pending.');
        }

        $paymentService->completePayment($payment, 'cash_' . $payment->id);

        return redirect()->to($redirectUrl)
            ->with('success', 'Payment confirmed successfully.');
    }
}
