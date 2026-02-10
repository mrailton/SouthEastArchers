<?php

namespace App\Http\Controllers\PublicPages;

use App\Http\Controllers\Controller;
use App\Settings\ApplicationSettings;
use Illuminate\Http\Request;
use Illuminate\View\View;

class ShowMembershipInfoController extends Controller
{
    /**
     * Display the membership information page.
     */
    public function __invoke(Request $request, ApplicationSettings $settings): View
    {
        return view('public.membership', [
            'annualCost' => $settings->annual_membership_cost / 100,
            'shootsIncluded' => $settings->membership_shoots_included,
            'additionalShootCost' => $settings->additional_shoot_cost / 100,
        ]);
    }
}
