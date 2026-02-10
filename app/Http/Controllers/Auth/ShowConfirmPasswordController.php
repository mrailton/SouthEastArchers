<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use Illuminate\View\View;

class ShowConfirmPasswordController extends Controller
{
    /**
     * Show the confirm password view.
     */
    public function __invoke(): View
    {
        return view('auth.confirm-password');
    }
}
