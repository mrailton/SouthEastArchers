<?php

use App\Enums\MembershipStatus;
use App\Enums\PaymentMethod;
use App\Enums\PaymentStatus;
use App\Enums\PaymentType;
use App\Models\Membership;
use App\Models\Payment;
use App\Models\User;
use App\Services\PaymentService;
use App\Services\SumUpService;
use App\Settings\ApplicationSettings;
use Illuminate\Support\Facades\Mail;

beforeEach(function () {
    Mail::fake();
});

test('payment service creates cash membership payment', function () {
    $user = User::factory()->create();

    $service = app(PaymentService::class);
    $payment = $service->createCashMembershipPayment($user);

    expect($payment)->toBeInstanceOf(Payment::class)
        ->and($payment->payment_method)->toBe(PaymentMethod::Cash)
        ->and($payment->payment_type)->toBe(PaymentType::Membership)
        ->and($payment->status)->toBe(PaymentStatus::Pending);
});

test('payment service creates cash credit payment', function () {
    $user = User::factory()->create();

    $service = app(PaymentService::class);
    $payment = $service->createCashCreditPayment($user, 5);

    expect($payment)->toBeInstanceOf(Payment::class)
        ->and($payment->payment_method)->toBe(PaymentMethod::Cash)
        ->and($payment->payment_type)->toBe(PaymentType::Credits);
});

test('payment service calculates credit cost correctly', function () {
    $user = User::factory()->create();
    $settings = app(ApplicationSettings::class);

    $service = app(PaymentService::class);
    $payment = $service->createCashCreditPayment($user, 3);

    expect($payment->amount_cents)->toBe(3 * $settings->additional_shoot_cost);
});

test('payment service completes membership payment', function () {
    $user = User::factory()->create();

    $payment = Payment::factory()->create([
        'user_id' => $user->id,
        'payment_type' => PaymentType::Membership,
        'status' => PaymentStatus::Pending,
    ]);

    $service = app(PaymentService::class);
    $service->completePayment($payment, 'txn_123');

    $payment->refresh();
    expect($payment->status)->toBe(PaymentStatus::Completed)
        ->and($payment->external_transaction_id)->toBe('txn_123');

    // User should have membership now
    $user->refresh();
    expect($user->membership)->not->toBeNull();
});

test('payment service completes credit payment', function () {
    $user = User::factory()->create();
    $settings = app(ApplicationSettings::class);

    // Create membership first
    Membership::create([
        'user_id' => $user->id,
        'start_date' => now(),
        'expiry_date' => now()->addYear(),
        'initial_credits' => 20,
        'purchased_credits' => 0,
        'status' => MembershipStatus::Active,
    ]);

    // Calculate credits from payment
    $creditQuantity = 5;
    $amountCents = $creditQuantity * $settings->additional_shoot_cost;

    $payment = Payment::factory()->create([
        'user_id' => $user->id,
        'payment_type' => PaymentType::Credits,
        'amount_cents' => $amountCents,
        'status' => PaymentStatus::Pending,
    ]);

    $service = app(PaymentService::class);
    $service->completePayment($payment);

    $user->refresh();
    expect($user->membership->purchased_credits)->toBe(5);
});

test('payment service renews existing membership', function () {
    $user = User::factory()->create();

    // Create existing membership
    $membership = Membership::create([
        'user_id' => $user->id,
        'start_date' => now()->subMonths(6),
        'expiry_date' => now()->addMonths(6),
        'initial_credits' => 5,
        'purchased_credits' => 0,
        'status' => MembershipStatus::Active,
    ]);

    $payment = Payment::factory()->create([
        'user_id' => $user->id,
        'payment_type' => PaymentType::Membership,
        'status' => PaymentStatus::Pending,
    ]);

    $service = app(PaymentService::class);
    $service->completePayment($payment);

    $membership->refresh();
    $settings = app(ApplicationSettings::class);
    expect($membership->initial_credits)->toBe($settings->membership_shoots_included);
});

test('initiate membership payment with online returns checkout data', function () {
    $user = User::factory()->create();

    $mockSumUp = Mockery::mock(SumUpService::class);
    $mockSumUp->shouldReceive('createCheckout')->andReturn([
        'id' => 'checkout_123',
        'checkout_reference' => 'ref_123',
    ]);

    $this->app->instance(SumUpService::class, $mockSumUp);

    $service = app(PaymentService::class);
    $result = $service->initiateMembershipPayment($user, 'online');

    expect($result['success'])->toBeTrue()
        ->and($result['checkout_id'])->toBe('checkout_123');
});

test('initiate membership payment online fails without checkout creation', function () {
    $user = User::factory()->create();

    $mockSumUp = Mockery::mock(SumUpService::class);
    $mockSumUp->shouldReceive('createCheckout')->andReturn(null);

    $this->app->instance(SumUpService::class, $mockSumUp);

    $service = app(PaymentService::class);
    $result = $service->initiateMembershipPayment($user, 'online');

    expect($result['success'])->toBeFalse()
        ->and($result['error'])->toBeString();
});

test('initiate credit purchase with online returns checkout data', function () {
    $user = User::factory()->create();

    $mockSumUp = Mockery::mock(SumUpService::class);
    $mockSumUp->shouldReceive('createCheckout')->andReturn([
        'id' => 'checkout_456',
        'checkout_reference' => 'ref_456',
    ]);

    $this->app->instance(SumUpService::class, $mockSumUp);

    $service = app(PaymentService::class);
    $result = $service->initiateCreditPurchase($user, 5, 'online');

    expect($result['success'])->toBeTrue()
        ->and($result['checkout_id'])->toBe('checkout_456');
});

test('initiate credit purchase online fails without checkout creation', function () {
    $user = User::factory()->create();

    $mockSumUp = Mockery::mock(SumUpService::class);
    $mockSumUp->shouldReceive('createCheckout')->andReturn(null);

    $this->app->instance(SumUpService::class, $mockSumUp);

    $service = app(PaymentService::class);
    $result = $service->initiateCreditPurchase($user, 5, 'online');

    expect($result['success'])->toBeFalse()
        ->and($result['error'])->toBeString();
});

test('membership expiry is this year start when before membership year', function () {
    // Set membership year to start September 1
    $settings = app(ApplicationSettings::class);
    $settings->membership_year_start_month = 9;
    $settings->membership_year_start_day = 1;
    $settings->save();

    // Travel to a date before September (e.g., March 15)
    $this->travelTo(now()->setMonth(3)->setDay(15));

    $user = User::factory()->create();

    $payment = Payment::factory()->create([
        'user_id' => $user->id,
        'payment_type' => PaymentType::Membership,
        'status' => PaymentStatus::Pending,
    ]);

    $service = app(PaymentService::class);
    $service->completePayment($payment);

    $user->refresh();
    $membership = $user->membership;

    // Expiry should be Sept 1 of current year (since we're before Sept)
    expect($membership->expiry_date->month)->toBe(9)
        ->and($membership->expiry_date->day)->toBe(1);

    $this->travelBack();
});

test('membership expiry is next year start when after membership year start', function () {
    // Set membership year to start September 1
    $settings = app(ApplicationSettings::class);
    $settings->membership_year_start_month = 9;
    $settings->membership_year_start_day = 1;
    $settings->save();

    // Travel to a date after September (e.g., October 15)
    $this->travelTo(now()->setMonth(10)->setDay(15));

    $user = User::factory()->create();

    $payment = Payment::factory()->create([
        'user_id' => $user->id,
        'payment_type' => PaymentType::Membership,
        'status' => PaymentStatus::Pending,
    ]);

    $service = app(PaymentService::class);
    $service->completePayment($payment);

    $user->refresh();
    $membership = $user->membership;

    // Expiry should be Sept 1 of next year (since we're after Sept)
    expect($membership->expiry_date->month)->toBe(9)
        ->and($membership->expiry_date->day)->toBe(1)
        ->and($membership->expiry_date->year)->toBe(now()->year + 1);

    $this->travelBack();
});
