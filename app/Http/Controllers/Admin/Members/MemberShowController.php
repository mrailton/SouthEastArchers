<?php

namespace App\Http\Controllers\Admin\Members;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\View\View;

class MemberShowController extends Controller
{
    /**
     * Display a member's details.
     */
    public function __invoke(Request $request, User $user): View
    {
        $user->load(['membership', 'roles', 'shoots', 'payments', 'credits']);

        return view('admin.members.show', [
            'member' => $user,
        ]);
    }
}
