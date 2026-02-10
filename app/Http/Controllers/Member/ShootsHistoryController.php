<?php

namespace App\Http\Controllers\Member;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\View\View;

class ShootsHistoryController extends Controller
{
    /**
     * Display the member's shoot history.
     */
    public function __invoke(Request $request): View
    {
        $user = $request->user()->load('membership');

        $shoots = $user->shoots()
            ->orderByDesc('date')
            ->paginate(20);

        return view('member.shoots', [
            'user' => $user,
            'shoots' => $shoots,
        ]);
    }
}
