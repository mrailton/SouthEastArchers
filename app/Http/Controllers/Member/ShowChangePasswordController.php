<?php

namespace App\Http\Controllers\Member;

use App\Http\Controllers\Controller;
use Illuminate\View\View;

class ShowChangePasswordController extends Controller
{
    /**
     * Display the change password form.
     */
    public function __invoke(): View
    {
        return view('member.change-password');
    }
}
