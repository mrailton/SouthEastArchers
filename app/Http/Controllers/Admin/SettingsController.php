<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Settings\ApplicationSettings;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;

class SettingsController extends Controller
{
    /**
     * Display the settings form.
     */
    public function show(Request $request, ApplicationSettings $settings): View
    {
        return view('admin.settings', [
            'settings' => $settings,
        ]);
    }

    /**
     * Update the settings.
     */
    public function update(Request $request, ApplicationSettings $settings): RedirectResponse
    {
        $validated = $request->validate([
            'membership_year_start_month' => ['required', 'integer', 'min:1', 'max:12'],
            'membership_year_start_day' => ['required', 'integer', 'min:1', 'max:31'],
            'annual_membership_cost' => ['required', 'numeric', 'min:0'],
            'membership_shoots_included' => ['required', 'integer', 'min:0'],
            'additional_shoot_cost' => ['required', 'numeric', 'min:0'],
        ]);

        $settings->membership_year_start_month = $validated['membership_year_start_month'];
        $settings->membership_year_start_day = $validated['membership_year_start_day'];
        $settings->annual_membership_cost = (int) ($validated['annual_membership_cost'] * 100);
        $settings->membership_shoots_included = $validated['membership_shoots_included'];
        $settings->additional_shoot_cost = (int) ($validated['additional_shoot_cost'] * 100);
        $settings->save();

        return redirect()->route('admin.settings')
            ->with('success', 'Settings updated successfully.');
    }
}
