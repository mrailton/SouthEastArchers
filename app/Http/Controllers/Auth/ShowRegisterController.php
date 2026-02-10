<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use Illuminate\View\View;

class ShowRegisterController extends Controller
{
    /**
     * Display the registration view.
     */
    public function __invoke(): View
    {
        return view('auth.register');
    }
}
