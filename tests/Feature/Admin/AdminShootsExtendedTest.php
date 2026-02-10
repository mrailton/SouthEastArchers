<?php

use App\Models\Membership;
use App\Models\Shoot;
use App\Models\User;
use Spatie\Permission\Models\Permission;
use Spatie\Permission\Models\Role;

beforeEach(function () {
    Permission::findOrCreate('admin.dashboard.view');
    Permission::findOrCreate('shoots.read');
    Permission::findOrCreate('shoots.create');
    Permission::findOrCreate('shoots.update');

    $adminRole = Role::findOrCreate('Admin');
    $adminRole->givePermissionTo(Permission::all());
});

test('admin can add attendees to a shoot', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    // Create member with membership
    $member = User::factory()->create(['is_active' => true]);
    Membership::create([
        'user_id' => $member->id,
        'start_date' => now(),
        'expiry_date' => now()->addYear(),
        'initial_credits' => 20,
        'purchased_credits' => 0,
        'status' => \App\Enums\MembershipStatus::Active,
    ]);

    $response = $this->actingAs($admin)->post('/admin/shoots', [
        'date' => now()->addDays(7)->format('Y-m-d'),
        'location' => 'Hall',
        'description' => 'Test shoot with attendees',
        'attendees' => [$member->id],
    ]);

    $response->assertRedirect();

    $shoot = Shoot::where('description', 'Test shoot with attendees')->first();
    expect($shoot)->not->toBeNull()
        ->and($shoot->users)->toHaveCount(1);

    // Member should have credit deducted
    $member->refresh();
    expect($member->membership->initial_credits)->toBe(19);
});

test('admin can update shoot with attendees', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $shoot = Shoot::factory()->create();

    $member1 = User::factory()->create(['is_active' => true]);
    $member2 = User::factory()->create(['is_active' => true]);

    $response = $this->actingAs($admin)->put("/admin/shoots/{$shoot->id}", [
        'date' => $shoot->date->format('Y-m-d'),
        'location' => 'Meadow',
        'description' => 'Updated shoot',
        'attendees' => [$member1->id, $member2->id],
    ]);

    $response->assertRedirect();

    $shoot->refresh();
    expect($shoot->users)->toHaveCount(2);
});

test('shoot validation requires date and location', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $response = $this->actingAs($admin)->post('/admin/shoots', [
        'description' => 'Missing required fields',
    ]);

    $response->assertSessionHasErrors(['date', 'location']);
});
