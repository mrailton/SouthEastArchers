<?php

namespace App\Http\Controllers\Admin\Roles;

use App\Http\Controllers\Controller;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Spatie\Permission\Models\Role;

class DeleteRoleController extends Controller
{
    /**
     * Delete a role.
     */
    public function __invoke(Request $request, Role $role): RedirectResponse
    {
        if ($role->name === 'Admin') {
            return redirect()->route('admin.roles.index')
                ->with('error', 'Cannot delete the Admin role.');
        }

        $role->delete();

        return redirect()->route('admin.roles.index')
            ->with('success', 'Role deleted successfully.');
    }
}
