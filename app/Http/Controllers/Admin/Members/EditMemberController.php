<?php

namespace App\Http\Controllers\Admin\Members;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\View\View;
use Spatie\Permission\Models\Role;

class EditMemberController extends Controller
{
    /**
     * Display the edit member form.
     */
    public function __invoke(User $user): View
    {
        $user->load(['membership', 'roles']);

        return view('admin.members.edit', [
            'member' => $user,
            'roles' => Role::all(),
        ]);
    }
}
