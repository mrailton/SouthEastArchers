<?php

namespace App\Http\Controllers\Payment;

use App\Http\Controllers\Controller;
use Illuminate\View\View;

class ShowCheckoutController extends Controller
{
    /**
     * Display the checkout page.
     */
    public function __invoke(string $checkoutId): View
    {
        $amount = session('checkout_amount', 0.00);
        $description = session('checkout_description', 'Payment');

        return view('payment.checkout', [
            'checkoutId' => $checkoutId,
            'amount' => $amount,
            'description' => $description,
        ]);
    }
}
