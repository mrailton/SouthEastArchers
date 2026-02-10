<?php

namespace App\Http\Controllers\PublicPages;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\View\View;

class AboutController extends Controller
{
    /**
     * Display the about page.
     */
    public function __invoke(Request $request): View
    {
        return view('public.about');
    }
}
