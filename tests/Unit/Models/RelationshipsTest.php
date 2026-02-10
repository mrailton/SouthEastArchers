<?php

use App\Models\Credit;
use App\Models\Membership;
use App\Models\Payment;
use App\Models\Shoot;
use App\Models\User;

test('user has many shoots relationship', function () {
    $user = User::factory()->create();
    $shoot = Shoot::factory()->create();
    $user->shoots()->attach($shoot->id);

    expect($user->shoots)->toHaveCount(1);
});

test('user has many payments relationship', function () {
    $user = User::factory()->create();
    Payment::factory()->create(['user_id' => $user->id]);
    Payment::factory()->create(['user_id' => $user->id]);

    expect($user->payments)->toHaveCount(2);
});

test('user has many credits relationship', function () {
    $user = User::factory()->create();
    Credit::factory()->create(['user_id' => $user->id]);

    expect($user->credits)->toHaveCount(1);
});

test('user has one membership relationship', function () {
    $user = User::factory()->create();
    Membership::factory()->create(['user_id' => $user->id]);

    expect($user->membership)->not->toBeNull();
});

test('shoot has many users relationship', function () {
    $shoot = Shoot::factory()->create();
    $user1 = User::factory()->create();
    $user2 = User::factory()->create();

    $shoot->users()->attach([$user1->id, $user2->id]);

    expect($shoot->users)->toHaveCount(2);
});

test('payment belongs to user relationship', function () {
    $user = User::factory()->create(['name' => 'Test User']);
    $payment = Payment::factory()->create(['user_id' => $user->id]);

    expect($payment->user->name)->toBe('Test User');
});

test('credit belongs to user relationship', function () {
    $user = User::factory()->create(['name' => 'Credit User']);
    $credit = Credit::factory()->create(['user_id' => $user->id]);

    expect($credit->user->name)->toBe('Credit User');
});

test('membership belongs to user relationship', function () {
    $user = User::factory()->create(['name' => 'Member User']);
    $membership = Membership::factory()->create(['user_id' => $user->id]);

    expect($membership->user->name)->toBe('Member User');
});

test('credit belongs to payment relationship', function () {
    $user = User::factory()->create();
    $payment = Payment::factory()->create(['user_id' => $user->id]);
    $credit = Credit::factory()->create([
        'user_id' => $user->id,
        'payment_id' => $payment->id,
    ]);

    expect($credit->payment)->not->toBeNull()
        ->and($credit->payment->id)->toBe($payment->id);
});

test('payment has many credits relationship', function () {
    $user = User::factory()->create();
    $payment = Payment::factory()->create(['user_id' => $user->id]);
    Credit::factory()->create([
        'user_id' => $user->id,
        'payment_id' => $payment->id,
    ]);
    Credit::factory()->create([
        'user_id' => $user->id,
        'payment_id' => $payment->id,
    ]);

    expect($payment->credits)->toHaveCount(2);
});
