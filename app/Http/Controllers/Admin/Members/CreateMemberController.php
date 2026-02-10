<?php

namespace App\Http\Controllers\Admin\Members;

use App\Http\Controllers\Controller;
use Illuminate\View\View;
use Spatie\Permission\Models\Role;

class CreateMemberController extends Controller
{
    /**
     * Display the create member form.
     */
    public function __invoke(): View
    {
        return view('admin.members.create', [
            'roles' => Role::all(),
        ]);
    }
}
