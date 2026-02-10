<?php

namespace App\Http\Controllers\Admin\Members;

use App\Enums\MembershipStatus;
use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;

class ActivateMembershipController extends Controller
{
    /**
     * Activate a user's pending membership.
     */
    public function __invoke(Request $request, User $user): RedirectResponse
    {
        $membership = $user->membership;

        if (! $membership) {
            return redirect()->route('admin.members.show', $user)
                ->with('error', 'User has no membership to activate.');
        }

        if ($membership->status !== MembershipStatus::Pending) {
            return redirect()->route('admin.members.show', $user)
                ->with('error', 'Membership is not pending.');
        }

        $membership->activate();

        return redirect()->route('admin.members.show', $user)
            ->with('success', 'Membership activated successfully.');
    }
}
