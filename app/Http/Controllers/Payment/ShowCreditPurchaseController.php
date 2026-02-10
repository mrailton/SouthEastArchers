<?php

namespace App\Http\Controllers\Payment;

use App\Http\Controllers\Controller;
use App\Settings\ApplicationSettings;
use Illuminate\View\View;

class ShowCreditPurchaseController extends Controller
{
    /**
     * Display the credit purchase page.
     */
    public function __invoke(ApplicationSettings $settings): View
    {
        return view('payment.credits', [
            'creditCost' => $settings->additional_shoot_cost / 100.0,
        ]);
    }
}
