<?php

namespace App\Http\Controllers\Admin\Events;

use App\Http\Controllers\Controller;
use App\Models\Event;
use Illuminate\Http\Request;
use Illuminate\View\View;

class EventsIndexController extends Controller
{
    /**
     * Display the events list.
     */
    public function __invoke(Request $request): View
    {
        $events = Event::orderByDesc('start_date')
            ->paginate(20);

        return view('admin.events.index', [
            'events' => $events,
        ]);
    }
}
