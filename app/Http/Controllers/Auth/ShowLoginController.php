<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use Illuminate\View\View;

class ShowLoginController extends Controller
{
    /**
     * Display the login view.
     */
    public function __invoke(): View
    {
        return view('auth.login');
    }
}
