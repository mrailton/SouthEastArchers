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

class ShootEditController extends Controller
{
    /**
     * Display the edit shoot form.
     */
    public function show(Request $request, Shoot $shoot): View
    {
        $shoot->load('users');

        $members = User::where('is_active', true)
            ->orderBy('name')
            ->get();

        $locations = ShootLocation::cases();

        return view('admin.shoots.edit', [
            'shoot' => $shoot,
            'members' => $members,
            'locations' => $locations,
        ]);
    }

    /**
     * Update the shoot.
     */
    public function update(Request $request, Shoot $shoot): RedirectResponse
    {
        $validated = $request->validate([
            'date' => ['required', 'date'],
            'location' => ['required', Rule::enum(ShootLocation::class)],
            'description' => ['nullable', 'string', 'max:500'],
            'attendees' => ['nullable', 'array'],
            'attendees.*' => ['exists:users,id'],
        ]);

        $shoot->update([
            'date' => $validated['date'],
            'location' => $validated['location'],
            'description' => $validated['description'] ?? null,
        ]);

        // Update attendees
        $newAttendees = $validated['attendees'] ?? [];
        $currentAttendees = $shoot->users->pluck('id')->toArray();

        // Find newly added attendees
        $addedAttendees = array_diff($newAttendees, $currentAttendees);
        $removedAttendees = array_diff($currentAttendees, $newAttendees);

        // Deduct credits for new attendees
        foreach ($addedAttendees as $userId) {
            /** @var User|null $attendeeUser */
            $attendeeUser = User::with('membership')->find($userId);
            if ($attendeeUser?->membership) {
                $attendeeUser->membership->useCredit();
            }
        }

        // Refund credits for removed attendees
        foreach ($removedAttendees as $userId) {
            /** @var User|null $removedUser */
            $removedUser = User::with('membership')->find($userId);
            if ($removedUser?->membership) {
                $removedUser->membership->addCredits(1);
            }
        }

        // Sync attendees
        $attendeeData = [];
        foreach ($newAttendees as $userId) {
            $attendeeData[$userId] = ['attended_at' => now()];
        }
        $shoot->users()->sync($attendeeData);

        return redirect()->route('admin.shoots.index')
            ->with('success', 'Shoot updated successfully.');
    }
}
