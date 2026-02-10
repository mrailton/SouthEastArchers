<?php

namespace App\Http\Controllers\Member;

use App\Http\Controllers\Controller;
use App\Settings\ApplicationSettings;
use Illuminate\Http\Request;
use Illuminate\View\View;

class ShowCreditsController extends Controller
{
    /**
     * Display the member's credits page.
     */
    public function __invoke(Request $request, ApplicationSettings $settings): View
    {
        $user = $request->user()->load(['membership', 'credits.payment']);

        $credits = $user->credits()
            ->with('payment')
            ->orderByDesc('created_at')
            ->get();

        return view('member.credits', [
            'user' => $user,
            'credits' => $credits,
            'additionalShootCost' => $settings->additional_shoot_cost / 100,
        ]);
    }
}
