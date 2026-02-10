<?php

namespace App\Http\Controllers\Member;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\View\View;

class DashboardController extends Controller
{
    /**
     * Display the member dashboard.
     */
    public function __invoke(Request $request): View
    {
        $user = $request->user()->load(['membership', 'shoots']);

        $shootsAttended = $user->shoots()->count();

        return view('member.dashboard', [
            'user' => $user,
            'membership' => $user->membership,
            'shootsAttended' => $shootsAttended,
        ]);
    }
}
