<?php

namespace App\Http\Controllers\PublicPages;

use App\Http\Controllers\Controller;
use App\Models\Event;
use Illuminate\Http\Request;
use Illuminate\View\View;

class EventsController extends Controller
{
    /**
     * Display the events page.
     */
    public function __invoke(Request $request): View
    {
        $events = Event::where('published', true)
            ->where('start_date', '>=', now())
            ->orderBy('start_date')
            ->paginate(10);

        return view('public.events', [
            'events' => $events,
        ]);
    }
}
