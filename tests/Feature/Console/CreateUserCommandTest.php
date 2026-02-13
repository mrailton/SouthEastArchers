<?php

use App\Models\User;

use function Pest\Laravel\artisan;

use Spatie\Permission\Models\Role;

beforeEach(function () {
    Role::create(['name' => 'Admin', 'guard_name' => 'web']);
    Role::create(['name' => 'Content Manager', 'guard_name' => 'web']);
});

test('user:create command creates a user with all required fields', function () {
    artisan('user:create')
        ->expectsQuestion('Name', 'John Doe')
        ->expectsQuestion('Email', 'john@example.com')
        ->expectsQuestion('Phone Number (optional)', '0851234567')
        ->expectsQuestion('Password', 'password123')
        ->expectsQuestion('Confirm Password', 'password123')
        ->expectsQuestion('Qualification', 'beginner')
        ->expectsQuestion('Select roles to assign', [])
        ->expectsOutputToContain("User 'John Doe' created successfully")
        ->assertSuccessful();

    $user = User::where('email', 'john@example.com')->first();

    expect($user)->not->toBeNull()
        ->and($user->name)->toBe('John Doe')
        ->and($user->phone)->toBe('0851234567')
        ->and($user->qualification)->toBe('beginner')
        ->and($user->is_active)->toBeTrue();
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

test('user:create command assigns selected roles', function () {
    $adminRole = Role::where('name', 'Admin')->first();
    $contentRole = Role::where('name', 'Content Manager')->first();

    artisan('user:create')
        ->expectsQuestion('Name', 'Admin User')
        ->expectsQuestion('Email', 'admin@example.com')
        ->expectsQuestion('Phone Number (optional)', '')
        ->expectsQuestion('Password', 'password123')
        ->expectsQuestion('Confirm Password', 'password123')
        ->expectsQuestion('Qualification', 'ai')
        ->expectsQuestion('Select roles to assign', [$adminRole->id, $contentRole->id])
        ->expectsOutputToContain('Assigned roles: Admin, Content Manager')
        ->assertSuccessful();

    $user = User::where('email', 'admin@example.com')->first();

    expect($user)->not->toBeNull()
        ->and($user->hasRole('Admin'))->toBeTrue()
        ->and($user->hasRole('Content Manager'))->toBeTrue();
});

test('user:create command stores email in lowercase', function () {
    artisan('user:create')
        ->expectsQuestion('Name', 'Test User')
        ->expectsQuestion('Email', 'TEST@EXAMPLE.COM')
        ->expectsQuestion('Phone Number (optional)', '')
        ->expectsQuestion('Password', 'password123')
        ->expectsQuestion('Confirm Password', 'password123')
        ->expectsQuestion('Qualification', 'ifaf')
        ->expectsQuestion('Select roles to assign', [])
        ->assertSuccessful();

    expect(User::where('email', 'test@example.com')->exists())->toBeTrue();
});

test('user:create command creates activated user', function () {
    artisan('user:create')
        ->expectsQuestion('Name', 'Active User')
        ->expectsQuestion('Email', 'active@example.com')
        ->expectsQuestion('Phone Number (optional)', '')
        ->expectsQuestion('Password', 'password123')
        ->expectsQuestion('Confirm Password', 'password123')
        ->expectsQuestion('Qualification', 'beginner')
        ->expectsQuestion('Select roles to assign', [])
        ->assertSuccessful();

    $user = User::where('email', 'active@example.com')->first();

    expect($user->is_active)->toBeTrue();
});

test('user:create command hashes password', function () {
    artisan('user:create')
        ->expectsQuestion('Name', 'Password User')
        ->expectsQuestion('Email', 'password@example.com')
        ->expectsQuestion('Phone Number (optional)', '')
        ->expectsQuestion('Password', 'mypassword')
        ->expectsQuestion('Confirm Password', 'mypassword')
        ->expectsQuestion('Qualification', 'beginner')
        ->expectsQuestion('Select roles to assign', [])
        ->assertSuccessful();

    $user = User::where('email', 'password@example.com')->first();

    expect($user->password)->not->toBe('mypassword')
        ->and(password_verify('mypassword', $user->password))->toBeTrue();
});
