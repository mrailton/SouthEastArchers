<?php

namespace App\Http\Controllers\Admin\Shoots;

use App\Enums\ShootLocation;
use App\Http\Controllers\Controller;
use App\Models\Shoot;
use App\Models\User;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;
use Illuminate\View\View;

class ShootCreateController extends Controller
{
    /**
     * Display the create shoot form.
     */
    public function show(Request $request): View
    {
        $members = User::where('is_active', true)
            ->orderBy('name')
            ->get();

        $locations = ShootLocation::cases();

        return view('admin.shoots.create', [
            'members' => $members,
            'locations' => $locations,
        ]);
    }

    /**
     * Store a new shoot.
     */
    public function store(Request $request): RedirectResponse
    {
        $validated = $request->validate([
            'date' => ['required', 'date'],
            'location' => ['required', Rule::enum(ShootLocation::class)],
            'description' => ['nullable', 'string', 'max:500'],
            'attendees' => ['nullable', 'array'],
            'attendees.*' => ['exists:users,id'],
        ]);

        $shoot = Shoot::create([
            'date' => $validated['date'],
            'location' => $validated['location'],
            'description' => $validated['description'] ?? null,
        ]);

        if (! empty($validated['attendees'])) {
            $attendeeData = [];
            foreach ($validated['attendees'] as $userId) {
                $attendeeData[$userId] = ['attended_at' => now()];

                // Deduct credit from user's membership
                /** @var User|null $attendeeUser */
                $attendeeUser = User::with('membership')->find($userId);
                if ($attendeeUser?->membership) {
                    $attendeeUser->membership->useCredit();
                }
            }
            $shoot->users()->attach($attendeeData);
        }

        return redirect()->route('admin.shoots.index')
            ->with('success', 'Shoot created successfully.');
    }
}
