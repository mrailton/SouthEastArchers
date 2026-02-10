<?php

use App\Mail\AccountActivatedMail;
use App\Models\User;
use Illuminate\Support\Facades\Mail;
use Spatie\Permission\Models\Permission;
use Spatie\Permission\Models\Role;

beforeEach(function () {
    // Create required permissions
    Permission::findOrCreate('admin.dashboard.view');
    Permission::findOrCreate('members.read');
    Permission::findOrCreate('members.create');
    Permission::findOrCreate('members.update');
    Permission::findOrCreate('members.activate_account');
    Permission::findOrCreate('members.manage_membership');

    // Create admin role with permissions
    $adminRole = Role::findOrCreate('Admin');
    $adminRole->givePermissionTo([
        'admin.dashboard.view',
        'members.read',
        'members.create',
        'members.update',
        'members.activate_account',
        'members.manage_membership',
    ]);
});

test('admin dashboard requires authentication', function () {
    $this->get('/admin')->assertRedirect('/login');
});

test('admin dashboard requires admin permission', function () {
    $user = User::factory()->create(['is_active' => true]);

    $this->actingAs($user)->get('/admin')->assertForbidden();
});

test('admin can access dashboard', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $this->actingAs($admin)->get('/admin')->assertSuccessful();
});

test('admin can view members list', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    User::factory()->count(3)->create();

    $this->actingAs($admin)
        ->get('/admin/members')
        ->assertSuccessful();
});

test('admin can view member details', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $member = User::factory()->create(['name' => 'Test Member']);

    $this->actingAs($admin)
        ->get("/admin/members/{$member->id}")
        ->assertSuccessful()
        ->assertSee('Test Member');
});

test('admin can create new member', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $this->actingAs($admin)
        ->get('/admin/members/create')
        ->assertSuccessful();

    $response = $this->actingAs($admin)->post('/admin/members', [
        'name' => 'New Member',
        'email' => 'newmember@example.com',
        'phone' => '0851234567',
        'password' => 'password',
        'password_confirmation' => 'password',
        'qualification' => 'beginner',
        'is_active' => true,
    ]);

    $response->assertRedirect();
    expect(User::where('email', 'newmember@example.com')->exists())->toBeTrue();
});

test('admin can edit member', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $member = User::factory()->create();

    $this->actingAs($admin)
        ->get("/admin/members/{$member->id}/edit")
        ->assertSuccessful();

    $response = $this->actingAs($admin)->put("/admin/members/{$member->id}", [
        'name' => 'Updated Name',
        'email' => $member->email,
        'phone' => '0871234567',
        'qualification' => 'ai',
        'is_active' => true,
    ]);

    $response->assertRedirect();
    expect($member->fresh()->name)->toBe('Updated Name');
});

test('admin can activate account and sends email', function () {
    Mail::fake();

    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $member = User::factory()->create(['is_active' => false]);

    $response = $this->actingAs($admin)
        ->post("/admin/members/{$member->id}/activate");

    $response->assertRedirect();
    expect($member->fresh()->is_active)->toBeTrue();

    Mail::assertSent(AccountActivatedMail::class, fn ($mail) => $mail->hasTo($member->email));
});
