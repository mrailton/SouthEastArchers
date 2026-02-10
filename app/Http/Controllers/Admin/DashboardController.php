<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Membership;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\View\View;

class DashboardController extends Controller
{
    /**
     * Display the admin dashboard.
     */
    public function __invoke(Request $request): View
    {
        $totalMembers = User::count();

        $activeMemberships = Membership::where('status', 'active')
            ->where('expiry_date', '>=', now())
            ->count();

        $expiringSoon = Membership::where('status', 'active')
            ->whereBetween('expiry_date', [now(), now()->addDays(30)])
            ->count();

        $recentMembers = User::latest()
            ->take(5)
            ->get();

        return view('admin.dashboard', [
            'totalMembers' => $totalMembers,
            'activeMemberships' => $activeMemberships,
            'expiringSoon' => $expiringSoon,
            'recentMembers' => $recentMembers,
        ]);
    }
}
