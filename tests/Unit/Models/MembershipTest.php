<?php

use App\Enums\MembershipStatus;
use App\Models\Membership;
use App\Models\User;

test('membership can be created', function () {
    $user = User::factory()->create();

    $membership = Membership::create([
        'user_id' => $user->id,
        'start_date' => now(),
        'expiry_date' => now()->addYear(),
        'initial_credits' => 20,
        'purchased_credits' => 0,
        'status' => MembershipStatus::Active,
    ]);

    expect($membership)->not->toBeNull()
        ->and($membership->user_id)->toBe($user->id);
});

test('membership isActive returns true for active membership', function () {
    $user = User::factory()->create();

    $membership = Membership::create([
        'user_id' => $user->id,
        'start_date' => now()->subMonth(),
        'expiry_date' => now()->addMonths(11),
        'initial_credits' => 20,
        'purchased_credits' => 0,
        'status' => MembershipStatus::Active,
    ]);

    expect($membership->isActive())->toBeTrue();
});

test('membership isActive returns false for expired membership', function () {
    $user = User::factory()->create();

    $membership = Membership::create([
        'user_id' => $user->id,
        'start_date' => now()->subYear()->subMonth(),
        'expiry_date' => now()->subMonth(),
        'initial_credits' => 20,
        'purchased_credits' => 0,
        'status' => MembershipStatus::Active,
    ]);

    expect($membership->isActive())->toBeFalse();
});

test('membership isActive returns false for pending status', function () {
    $user = User::factory()->create();

    $membership = Membership::create([
        'user_id' => $user->id,
        'start_date' => now(),
        'expiry_date' => now()->addYear(),
        'initial_credits' => 20,
        'purchased_credits' => 0,
        'status' => MembershipStatus::Pending,
    ]);

    expect($membership->isActive())->toBeFalse();
});

test('membership creditsRemaining calculates correctly', function () {
    $user = User::factory()->create();

    $membership = Membership::create([
        'user_id' => $user->id,
        'start_date' => now(),
        'expiry_date' => now()->addYear(),
        'initial_credits' => 20,
        'purchased_credits' => 5,
        'status' => MembershipStatus::Active,
    ]);

    expect($membership->creditsRemaining())->toBe(25);
});

test('membership useCredit decreases credits', function () {
    $user = User::factory()->create();

    $membership = Membership::create([
        'user_id' => $user->id,
        'start_date' => now(),
        'expiry_date' => now()->addYear(),
        'initial_credits' => 20,
        'purchased_credits' => 5,
        'status' => MembershipStatus::Active,
    ]);

    $result = $membership->useCredit();

    expect($result)->toBeTrue()
        ->and($membership->fresh()->creditsRemaining())->toBe(24);
});

test('membership useCredit returns false when no credits', function () {
    $user = User::factory()->create();

    $membership = Membership::create([
        'user_id' => $user->id,
        'start_date' => now(),
        'expiry_date' => now()->addYear(),
        'initial_credits' => 0,
        'purchased_credits' => 0,
        'status' => MembershipStatus::Active,
    ]);

    expect($membership->useCredit())->toBeFalse();
});

test('membership addCredits increases purchased credits', function () {
    $user = User::factory()->create();

    $membership = Membership::create([
        'user_id' => $user->id,
        'start_date' => now(),
        'expiry_date' => now()->addYear(),
        'initial_credits' => 20,
        'purchased_credits' => 0,
        'status' => MembershipStatus::Active,
    ]);

    $membership->addCredits(10);

    expect($membership->fresh()->purchased_credits)->toBe(10);
});

test('use credit with allow negative deducts from initial when active', function () {
    $user = User::factory()->create();

    $membership = Membership::create([
        'user_id' => $user->id,
        'start_date' => now(),
        'expiry_date' => now()->addYear(),
        'initial_credits' => 0,
        'purchased_credits' => 0,
        'status' => MembershipStatus::Active,
    ]);

    $result = $membership->useCredit(allowNegative: true);

    expect($result)->toBeTrue()
        ->and($membership->fresh()->initial_credits)->toBe(-1);
});

test('use credit uses purchased credits when initial are zero', function () {
    $user = User::factory()->create();

    $membership = Membership::create([
        'user_id' => $user->id,
        'start_date' => now(),
        'expiry_date' => now()->addYear(),
        'initial_credits' => 0,
        'purchased_credits' => 5,
        'status' => MembershipStatus::Active,
    ]);

    $result = $membership->useCredit();

    expect($result)->toBeTrue()
        ->and($membership->fresh()->purchased_credits)->toBe(4);
});

test('membership activate sets status to active', function () {
    $user = User::factory()->create();

    $membership = Membership::create([
        'user_id' => $user->id,
        'start_date' => now(),
        'expiry_date' => now()->addYear(),
        'initial_credits' => 20,
        'purchased_credits' => 0,
        'status' => MembershipStatus::Pending,
    ]);

    $membership->activate();

    expect($membership->fresh()->status)->toBe(MembershipStatus::Active);
});

test('membership expire initial credits sets to zero', function () {
    $user = User::factory()->create();

    $membership = Membership::create([
        'user_id' => $user->id,
        'start_date' => now(),
        'expiry_date' => now()->addYear(),
        'initial_credits' => 20,
        'purchased_credits' => 0,
        'status' => MembershipStatus::Active,
    ]);

    $membership->expireInitialCredits();

    expect($membership->initial_credits)->toBe(0);
});
