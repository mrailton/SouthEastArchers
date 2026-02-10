<?php

namespace App\Http\Controllers\Admin\Members;

use App\Http\Controllers\Controller;
use App\Models\User;
use App\Settings\ApplicationSettings;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;

class RenewMembershipController extends Controller
{
    /**
     * Renew a user's expired membership.
     */
    public function __invoke(Request $request, User $user, ApplicationSettings $settings): RedirectResponse
    {
        $membership = $user->membership;

        if (! $membership) {
            return redirect()->route('admin.members.show', $user)
                ->with('error', 'User has no membership to renew.');
        }

        $membership->renew($settings->membership_shoots_included);

        return redirect()->route('admin.members.show', $user)
            ->with('success', 'Membership renewed successfully.');
    }
}
