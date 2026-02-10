<?php

namespace App\Http\Controllers\PublicPages;

use App\Http\Controllers\Controller;
use App\Models\Event;
use Illuminate\Http\Request;
use Illuminate\View\View;

class HomeController extends Controller
{
    /**
     * Display the home page.
     */
    public function __invoke(Request $request): View
    {
        $upcomingEvents = Event::where('published', true)
            ->where('start_date', '>=', now())
            ->orderBy('start_date')
            ->take(3)
            ->get();

        return view('public.home', [
            'upcomingEvents' => $upcomingEvents,
        ]);
    }
}
