<?php

namespace App\Http\Controllers\Member;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\View\View;

class ShowProfileController extends Controller
{
    /**
     * Display the profile form.
     */
    public function __invoke(Request $request): View
    {
        return view('member.profile', [
            'user' => $request->user(),
        ]);
    }
}
