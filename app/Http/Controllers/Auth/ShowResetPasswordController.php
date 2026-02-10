<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\View\View;

class ShowResetPasswordController extends Controller
{
    /**
     * Display the password reset view.
     */
    public function __invoke(Request $request): View
    {
        return view('auth.reset-password', ['request' => $request]);
    }
}
