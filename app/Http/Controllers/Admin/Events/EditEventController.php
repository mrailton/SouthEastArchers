<?php

namespace App\Http\Controllers\Admin\Events;

use App\Http\Controllers\Controller;
use App\Models\Event;
use Illuminate\View\View;

class EditEventController extends Controller
{
    /**
     * Display the edit event form.
     */
    public function __invoke(Event $event): View
    {
        return view('admin.events.edit', [
            'event' => $event,
        ]);
    }
}
