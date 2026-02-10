<?php

namespace App\Http\Controllers\Admin\Roles;

use App\Http\Controllers\Controller;
use Illuminate\View\View;
use Spatie\Permission\Models\Permission;

class CreateRoleController extends Controller
{
    /**
     * Display the create role form.
     */
    public function __invoke(): View
    {
        return view('admin.roles.create', [
            'permissions' => Permission::all(),
        ]);
    }
}
