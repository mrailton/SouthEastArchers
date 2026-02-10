<?php

namespace App\Http\Controllers\Payment;

use App\Http\Controllers\Controller;
use App\Settings\ApplicationSettings;
use Illuminate\View\View;

class ShowMembershipPaymentController extends Controller
{
    /**
     * Display the membership payment page.
     */
    public function __invoke(ApplicationSettings $settings): View
    {
        return view('payment.membership', [
            'annualCost' => $settings->annual_membership_cost / 100.0,
            'shootsIncluded' => $settings->membership_shoots_included,
        ]);
    }
}
