<?php

use App\Models\Shoot;
use App\Models\User;

test('dashboard requires authentication', function () {
    $this->get('/dashboard')->assertRedirect('/login');
});

test('dashboard can be rendered for authenticated user', function () {
    $user = User::factory()->create(['is_active' => true]);

    $this->actingAs($user)->get('/dashboard')->assertSuccessful();
});

test('profile page can be rendered', function () {
    $user = User::factory()->create(['is_active' => true]);

    $this->actingAs($user)
        ->get('/profile')
        ->assertSuccessful()
        ->assertSee($user->name)
        ->assertSee($user->email);
});

test('profile can be updated', function () {
    $user = User::factory()->create(['is_active' => true]);

    $response = $this->actingAs($user)->put('/profile', [
        'name' => 'Updated Name',
        'email' => $user->email,
        'phone' => '0871234567',
    ]);

    $response->assertRedirect('/profile');
    expect($user->fresh()->name)->toBe('Updated Name')
        ->and($user->fresh()->phone)->toBe('0871234567');
});

test('shoots history page can be rendered', function () {
    $user = User::factory()->create(['is_active' => true]);
    $shoot = Shoot::factory()->create();
    $user->shoots()->attach($shoot->id);

    $this->actingAs($user)
        ->get('/shoots')
        ->assertSuccessful();
});

test('credits page can be rendered', function () {
    $user = User::factory()->create(['is_active' => true]);

    $this->actingAs($user)
        ->get('/credits')
        ->assertSuccessful();
});

test('change password page can be rendered', function () {
    $user = User::factory()->create(['is_active' => true]);

    $this->actingAs($user)
        ->get('/change-password')
        ->assertSuccessful();
});

test('password can be changed', function () {
    $user = User::factory()->create(['is_active' => true]);

    $response = $this->actingAs($user)->put('/change-password', [
        'current_password' => 'password',
        'password' => 'new-password',
        'password_confirmation' => 'new-password',
    ]);

    $response->assertRedirect('/profile');
    expect(password_verify('new-password', $user->fresh()->password))->toBeTrue();
});

test('password change requires current password', function () {
    $user = User::factory()->create(['is_active' => true]);

    $response = $this->actingAs($user)->put('/change-password', [
        'current_password' => 'wrong-password',
        'password' => 'new-password',
        'password_confirmation' => 'new-password',
    ]);

    $response->assertSessionHasErrors(['current_password']);
});
