<?php

namespace App\Http\Controllers\Admin\Members;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Rules;
use Illuminate\View\View;
use Spatie\Permission\Models\Role;

class MemberCreateController extends Controller
{
    /**
     * Display the create member form.
     */
    public function show(Request $request): View
    {
        $roles = Role::all();

        return view('admin.members.create', [
            'roles' => $roles,
        ]);
    }

    /**
     * Store a new member.
     */
    public function store(Request $request): RedirectResponse
    {
        $validated = $request->validate([
            'name' => ['required', 'string', 'max:255'],
            'email' => ['required', 'string', 'lowercase', 'email', 'max:255', 'unique:users'],
            'phone' => ['nullable', 'string', 'max:50'],
            'password' => ['required', 'confirmed', Rules\Password::defaults()],
            'qualification' => ['required', 'string', 'in:none,beginner,ai,ifaf'],
            'is_active' => ['boolean'],
            'roles' => ['nullable', 'array'],
            'roles.*' => ['exists:roles,name'],
        ]);

        $user = User::create([
            'name' => $validated['name'],
            'email' => $validated['email'],
            'phone' => $validated['phone'] ?? '',
            'password' => Hash::make($validated['password']),
            'qualification' => $validated['qualification'],
            'is_active' => $validated['is_active'] ?? false,
        ]);

        if (! empty($validated['roles'])) {
            $user->syncRoles($validated['roles']);
        }

        return redirect()->route('admin.members.show', $user)
            ->with('success', 'Member created successfully.');
    }
}
