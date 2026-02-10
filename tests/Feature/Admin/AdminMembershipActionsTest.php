<?php

use App\Enums\MembershipStatus;
use App\Models\Membership;
use App\Models\User;
use Spatie\Permission\Models\Permission;
use Spatie\Permission\Models\Role;

beforeEach(function () {
    Permission::findOrCreate('admin.dashboard.view');
    Permission::findOrCreate('members.read');
    Permission::findOrCreate('members.manage_membership');

    $adminRole = Role::findOrCreate('Admin');
    $adminRole->givePermissionTo(Permission::all());
});

// ActivateMembershipController tests
test('admin can activate pending membership', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $user = User::factory()->create();
    Membership::create([
        'user_id' => $user->id,
        'start_date' => now(),
        'expiry_date' => now()->addYear(),
        'initial_credits' => 20,
        'purchased_credits' => 0,
        'status' => MembershipStatus::Pending,
    ]);

    $this->actingAs($admin)
        ->post(route('admin.members.membership.activate', $user))
        ->assertRedirect(route('admin.members.show', $user))
        ->assertSessionHas('success');

    $user->refresh();
    expect($user->membership->status)->toBe(MembershipStatus::Active);
});

test('activate membership fails when user has no membership', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $user = User::factory()->create();

    $this->actingAs($admin)
        ->post(route('admin.members.membership.activate', $user))
        ->assertRedirect(route('admin.members.show', $user))
        ->assertSessionHas('error', 'User has no membership to activate.');
});

test('activate membership fails when membership is not pending', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $user = User::factory()->create();
    Membership::create([
        'user_id' => $user->id,
        'start_date' => now(),
        'expiry_date' => now()->addYear(),
        'initial_credits' => 20,
        'purchased_credits' => 0,
        'status' => MembershipStatus::Active,
    ]);

    $this->actingAs($admin)
        ->post(route('admin.members.membership.activate', $user))
        ->assertRedirect(route('admin.members.show', $user))
        ->assertSessionHas('error', 'Membership is not pending.');
});

// RenewMembershipController tests
test('admin can renew membership', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $user = User::factory()->create();
    Membership::create([
        'user_id' => $user->id,
        'start_date' => now()->subYear(),
        'expiry_date' => now()->subMonth(),
        'initial_credits' => 0,
        'purchased_credits' => 0,
        'status' => MembershipStatus::Expired,
    ]);

    $this->actingAs($admin)
        ->post(route('admin.members.membership.renew', $user))
        ->assertRedirect(route('admin.members.show', $user))
        ->assertSessionHas('success');

    $user->refresh();
    expect($user->membership->status)->toBe(MembershipStatus::Active)
        ->and($user->membership->initial_credits)->toBe(20);
});

test('renew membership fails when user has no membership', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $user = User::factory()->create();

    $this->actingAs($admin)
        ->post(route('admin.members.membership.renew', $user))
        ->assertRedirect(route('admin.members.show', $user))
        ->assertSessionHas('error', 'User has no membership to renew.');
});
