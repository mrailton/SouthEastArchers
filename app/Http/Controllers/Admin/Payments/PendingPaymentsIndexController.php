<?php

namespace App\Http\Controllers\Admin\Payments;

use App\Enums\PaymentStatus;
use App\Http\Controllers\Controller;
use App\Models\Payment;
use Illuminate\Http\Request;
use Illuminate\View\View;

class PendingPaymentsIndexController extends Controller
{
    /**
     * Display the pending cash payments list.
     */
    public function __invoke(Request $request): View
    {
        $payments = Payment::with('user')
            ->where('payment_method', 'cash')
            ->where('status', PaymentStatus::Pending)
            ->orderBy('created_at')
            ->paginate(20);

        return view('admin.payments.pending', [
            'payments' => $payments,
        ]);
    }
}
