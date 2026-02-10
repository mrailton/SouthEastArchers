<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use Illuminate\View\View;

class ShowForgotPasswordController extends Controller
{
    /**
     * Display the password reset link request view.
     */
    public function __invoke(): View
    {
        return view('auth.forgot-password');
    }
}
