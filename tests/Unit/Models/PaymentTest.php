<?php

use App\Enums\PaymentMethod;
use App\Enums\PaymentStatus;
use App\Enums\PaymentType;
use App\Models\Payment;
use App\Models\User;

test('payment can be created', function () {
    $user = User::factory()->create();

    $payment = Payment::create([
        'user_id' => $user->id,
        'amount_cents' => 10000,
        'currency' => 'EUR',
        'payment_type' => PaymentType::Membership,
        'payment_method' => PaymentMethod::Online,
        'description' => 'Test payment',
        'status' => PaymentStatus::Pending,
    ]);

    expect($payment)->not->toBeNull()
        ->and($payment->amount_cents)->toBe(10000);
});

test('payment markCompleted updates status and transaction id', function () {
    $user = User::factory()->create();

    $payment = Payment::create([
        'user_id' => $user->id,
        'amount_cents' => 10000,
        'currency' => 'EUR',
        'payment_type' => PaymentType::Membership,
        'payment_method' => PaymentMethod::Online,
        'description' => 'Test payment',
        'status' => PaymentStatus::Pending,
    ]);

    $payment->markCompleted('txn_123', 'sumup');

    expect($payment->fresh()->status)->toBe(PaymentStatus::Completed)
        ->and($payment->fresh()->external_transaction_id)->toBe('txn_123')
        ->and($payment->fresh()->payment_processor)->toBe('sumup');
});

test('payment markFailed updates status', function () {
    $user = User::factory()->create();

    $payment = Payment::create([
        'user_id' => $user->id,
        'amount_cents' => 10000,
        'currency' => 'EUR',
        'payment_type' => PaymentType::Membership,
        'payment_method' => PaymentMethod::Online,
        'description' => 'Test payment',
        'status' => PaymentStatus::Pending,
    ]);

    $payment->markFailed();

    expect($payment->fresh()->status)->toBe(PaymentStatus::Failed);
});

test('payment amount accessor converts cents to euros', function () {
    $user = User::factory()->create();

    $payment = Payment::create([
        'user_id' => $user->id,
        'amount_cents' => 10050,
        'currency' => 'EUR',
        'payment_type' => PaymentType::Membership,
        'payment_method' => PaymentMethod::Online,
        'description' => 'Test payment',
        'status' => PaymentStatus::Pending,
    ]);

    expect($payment->amount)->toBe(100.50);
});

test('payment amount mutator converts euros to cents', function () {
    $user = User::factory()->create();

    $payment = Payment::create([
        'user_id' => $user->id,
        'amount_cents' => 0,
        'currency' => 'EUR',
        'payment_type' => PaymentType::Membership,
        'payment_method' => PaymentMethod::Online,
        'description' => 'Test payment',
        'status' => PaymentStatus::Pending,
    ]);

    $payment->amount = 50.75;
    $payment->save();

    expect($payment->fresh()->amount_cents)->toBe(5075);
});

test('payment belongs to user', function () {
    $user = User::factory()->create(['name' => 'Payment User']);

    $payment = Payment::create([
        'user_id' => $user->id,
        'amount_cents' => 10000,
        'currency' => 'EUR',
        'payment_type' => PaymentType::Membership,
        'payment_method' => PaymentMethod::Online,
        'description' => 'Test payment',
        'status' => PaymentStatus::Pending,
    ]);

    expect($payment->user->name)->toBe('Payment User');
});
