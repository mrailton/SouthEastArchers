<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Settings\ApplicationSettings;
use Illuminate\View\View;

class ShowSettingsController extends Controller
{
    /**
     * Display the settings form.
     */
    public function __invoke(ApplicationSettings $settings): View
    {
        return view('admin.settings', [
            'settings' => $settings,
        ]);
    }
}
