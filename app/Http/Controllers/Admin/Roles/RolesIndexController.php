<?php

namespace App\Http\Controllers\Admin\Roles;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\View\View;
use Spatie\Permission\Models\Permission;
use Spatie\Permission\Models\Role;

class RolesIndexController extends Controller
{
    /**
     * Display the roles list.
     */
    public function __invoke(Request $request): View
    {
        $roles = Role::with('permissions')->get();
        $permissions = Permission::all();

        return view('admin.roles.index', [
            'roles' => $roles,
            'permissions' => $permissions,
        ]);
    }
}
