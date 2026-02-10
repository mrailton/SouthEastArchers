<?php

namespace App\Http\Controllers\Payment;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\View\View;

class ShowPaymentHistoryController extends Controller
{
    public function __invoke(Request $request): View
    {
        /** @var \App\Models\User $user */
        $user = $request->user();

        $payments = $user->payments()
            ->orderByDesc('created_at')
            ->get();

        return view('payment.history', [
            'payments' => $payments,
        ]);
    }
}
