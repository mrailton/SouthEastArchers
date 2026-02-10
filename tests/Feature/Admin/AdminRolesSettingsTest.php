<?php

use App\Models\User;
use Spatie\Permission\Models\Permission;
use Spatie\Permission\Models\Role;

beforeEach(function () {
    Permission::findOrCreate('admin.dashboard.view');
    Permission::findOrCreate('roles.manage');
    Permission::findOrCreate('settings.read');
    Permission::findOrCreate('settings.write');

    $adminRole = Role::findOrCreate('Admin');
    $adminRole->givePermissionTo(Permission::all());
});

// Roles Tests
test('admin can view roles list', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $this->actingAs($admin)
        ->get('/admin/roles')
        ->assertSuccessful();
});

test('admin can create role', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $this->actingAs($admin)
        ->get('/admin/roles/create')
        ->assertSuccessful();

    $response = $this->actingAs($admin)->post('/admin/roles', [
        'name' => 'Test Role',
        'permissions' => [],
    ]);

    $response->assertRedirect();
    expect(Role::where('name', 'Test Role')->exists())->toBeTrue();
});

test('admin can edit role', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $role = Role::create(['name' => 'Editable Role']);

    $this->actingAs($admin)
        ->get("/admin/roles/{$role->id}/edit")
        ->assertSuccessful();

    $response = $this->actingAs($admin)->put("/admin/roles/{$role->id}", [
        'name' => 'Updated Role Name',
        'permissions' => [],
    ]);

    $response->assertRedirect();
    expect($role->fresh()->name)->toBe('Updated Role Name');
});

test('admin can delete role', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $role = Role::create(['name' => 'Deletable Role']);

    $response = $this->actingAs($admin)->delete("/admin/roles/{$role->id}");

    $response->assertRedirect();
    expect(Role::where('name', 'Deletable Role')->exists())->toBeFalse();
});

// Settings Tests
test('admin can view settings', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $this->actingAs($admin)
        ->get('/admin/settings')
        ->assertSuccessful();
});

test('admin can update settings', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $response = $this->actingAs($admin)->put('/admin/settings', [
        'membership_year_start_month' => 9,
        'membership_year_start_day' => 1,
        'annual_membership_cost' => 12000,
        'membership_shoots_included' => 25,
        'additional_shoot_cost' => 600,
    ]);

    $response->assertRedirect();
});

test('settings requires permission', function () {
    // Create user without settings permission
    Permission::findOrCreate('members.read');
    $memberRole = Role::findOrCreate('Member Manager');
    $memberRole->givePermissionTo(['admin.dashboard.view', 'members.read']);

    $user = User::factory()->create(['is_active' => true]);
    $user->assignRole('Member Manager');

    $this->actingAs($user)
        ->get('/admin/settings')
        ->assertForbidden();
});
