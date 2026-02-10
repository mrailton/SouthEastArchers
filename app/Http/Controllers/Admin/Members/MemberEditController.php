<?php

namespace App\Http\Controllers\Admin\Members;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;
use Illuminate\View\View;
use Spatie\Permission\Models\Role;

class MemberEditController extends Controller
{
    /**
     * Display the edit member form.
     */
    public function show(Request $request, User $user): View
    {
        $user->load(['membership', 'roles']);
        $roles = Role::all();

        return view('admin.members.edit', [
            'member' => $user,
            'roles' => $roles,
        ]);
    }

    /**
     * Update the member.
     */
    public function update(Request $request, User $user): RedirectResponse
    {
        $validated = $request->validate([
            'name' => ['required', 'string', 'max:255'],
            'email' => ['required', 'string', 'lowercase', 'email', 'max:255', Rule::unique('users')->ignore($user->id)],
            'phone' => ['nullable', 'string', 'max:50'],
            'qualification' => ['required', 'string', 'in:none,beginner,ai,ifaf'],
            'is_active' => ['boolean'],
            'roles' => ['nullable', 'array'],
            'roles.*' => ['exists:roles,name'],
        ]);

        $user->update([
            'name' => $validated['name'],
            'email' => $validated['email'],
            'phone' => $validated['phone'] ?? '',
            'qualification' => $validated['qualification'],
            'is_active' => $validated['is_active'] ?? false,
        ]);

        $user->syncRoles($validated['roles'] ?? []);

        return redirect()->route('admin.members.show', $user)
            ->with('success', 'Member updated successfully.');
    }
}
