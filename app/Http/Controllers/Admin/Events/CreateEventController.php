<?php

namespace App\Http\Controllers\Admin\Events;

use App\Http\Controllers\Controller;
use Illuminate\View\View;

class CreateEventController extends Controller
{
    /**
     * Display the create event form.
     */
    public function __invoke(): View
    {
        return view('admin.events.create');
    }
}
