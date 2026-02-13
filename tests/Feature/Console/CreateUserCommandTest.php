<?php

use App\Models\User;

use function Pest\Laravel\artisan;

use Spatie\Permission\Models\Role;

beforeEach(function () {
    Role::create(['name' => 'Admin', 'guard_name' => 'web']);
    Role::create(['name' => 'Content Manager', 'guard_name' => 'web']);
});

test('user:create command creates a user with all required fields', function () {
    $adminRole = Role::where('name', 'Admin')->first();
    $contentRole = Role::where('name', 'Content Manager')->first();

    artisan('user:create')
        ->expectsQuestion('Name', 'John Doe')
        ->expectsQuestion('Email', 'john@example.com')
        ->expectsQuestion('Phone Number (optional)', '0851234567')
        ->expectsQuestion('Password', 'password123')
        ->expectsQuestion('Confirm Password', 'password123')
        ->expectsQuestion('Qualification', 'beginner')
        ->expectsQuestion('Select roles to assign', [$adminRole->id, $contentRole->id])
        ->expectsOutputToContain("User 'John Doe' created successfully")
        ->assertSuccessful();

    $user = User::where('email', 'john@example.com')->first();

    expect($user)->not->toBeNull()
        ->and($user->name)->toBe('John Doe')
        ->and($user->phone)->toBe('0851234567')
        ->and($user->qualification)->toBe('beginner')
        ->and($user->is_active)->toBeTrue()
        ->and($user->password)->not->toBe('password123')
        ->and(password_verify('password123', $user->password))->toBeTrue()
        ->and($user->hasRole('Admin'))->toBeTrue()
        ->and($user->hasRole('Content Manager'))->toBeTrue();
});

test('user:create command creates user without phone number', function () {
    artisan('user:create')
        ->expectsQuestion('Name', 'Jane Doe')
        ->expectsQuestion('Email', 'jane@example.com')
        ->expectsQuestion('Phone Number (optional)', '')
        ->expectsQuestion('Password', 'password123')
        ->expectsQuestion('Confirm Password', 'password123')
        ->expectsQuestion('Qualification', 'none')
        ->expectsQuestion('Select roles to assign', [])
        ->assertSuccessful();

    $user = User::where('email', 'jane@example.com')->first();

    expect($user)->not->toBeNull()
        ->and($user->phone)->toBeNull();
});

test('user:create command validates email format', function () {
    artisan('user:create')
        ->expectsQuestion('Name', 'Invalid Email User')
        ->expectsQuestion('Email', 'invalid-email')
        ->expectsOutputToContain('Please enter a valid email address.')
        ->assertFailed();
});

test('user:create command validates email is not already registered', function () {
    User::factory()->create(['email' => 'existing@example.com']);

    artisan('user:create')
        ->expectsQuestion('Name', 'Duplicate Email User')
        ->expectsQuestion('Email', 'existing@example.com')
        ->expectsOutputToContain('This email is already registered.')
        ->assertFailed();
});
