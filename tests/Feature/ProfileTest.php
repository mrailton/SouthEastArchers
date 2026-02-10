<?php

use App\Models\User;

test('profile page is displayed', function () {
    $user = User::factory()->create(['is_active' => true]);

    $response = $this
        ->actingAs($user)
        ->get('/profile');

    $response->assertOk();
});

test('profile information can be updated', function () {
    $user = User::factory()->create(['is_active' => true]);

    $response = $this
        ->actingAs($user)
        ->put('/profile', [
            'name' => 'Updated User Name',
            'phone' => '0871234567',
        ]);

    $response
        ->assertSessionHasNoErrors()
        ->assertRedirect('/profile');

    $user->refresh();

    expect($user->name)->toBe('Updated User Name')
        ->and($user->phone)->toBe('0871234567');
});

test('profile update requires name', function () {
    $user = User::factory()->create(['is_active' => true]);

    $response = $this
        ->actingAs($user)
        ->put('/profile', [
            'phone' => '0871234567',
        ]);

    $response->assertSessionHasErrors(['name']);
});

test('profile shows success message after update', function () {
    $user = User::factory()->create(['is_active' => true]);

    $response = $this
        ->actingAs($user)
        ->put('/profile', [
            'name' => 'Test User',
        ]);

    $response->assertSessionHas('success', 'Profile updated successfully.');
});
