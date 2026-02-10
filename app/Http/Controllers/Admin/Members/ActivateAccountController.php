<?php

namespace App\Http\Controllers\Admin\Members;

use App\Http\Controllers\Controller;
use App\Mail\AccountActivatedMail;
use App\Models\User;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Mail;

class ActivateAccountController extends Controller
{
    /**
     * Activate a user's account.
     */
    public function __invoke(Request $request, User $user): RedirectResponse
    {
        $user->update(['is_active' => true]);

        Mail::to($user)->send(new AccountActivatedMail($user));

        return redirect()->route('admin.members.show', $user)
            ->with('success', 'Account activated successfully. Activation email sent.');
    }
}
