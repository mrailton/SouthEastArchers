<?php

use App\Enums\MembershipStatus;
use App\Enums\PaymentStatus;
use App\Enums\PaymentType;
use App\Models\Membership;
use App\Models\Payment;
use App\Models\User;
use App\Services\SumUpService;
use Illuminate\Support\Facades\Mail;

beforeEach(function () {
    Mail::fake();
});

test('online membership payment redirects to checkout when successful', function () {
    $user = User::factory()->create(['is_active' => true]);

    // Mock the SumUpService
    $sumUpMock = Mockery::mock(SumUpService::class);
    $sumUpMock->shouldReceive('createCheckout')->andReturn([
        'id' => 'checkout_123',
        'checkout_reference' => 'ref_123',
        'status' => 'PENDING',
    ]);

    $this->app->instance(SumUpService::class, $sumUpMock);

    $response = $this->actingAs($user)->post('/payment/membership', [
        'payment_method' => 'online',
    ]);

    $response->assertRedirect(route('payment.checkout', ['checkout_id' => 'checkout_123']));
});

test('online credit payment redirects to checkout when successful', function () {
    $user = User::factory()->create(['is_active' => true]);

    $sumUpMock = Mockery::mock(SumUpService::class);
    $sumUpMock->shouldReceive('createCheckout')->andReturn([
        'id' => 'checkout_456',
        'checkout_reference' => 'ref_456',
        'status' => 'PENDING',
    ]);

    $this->app->instance(SumUpService::class, $sumUpMock);

    $response = $this->actingAs($user)->post('/payment/credits', [
        'quantity' => 10,
        'payment_method' => 'online',
    ]);

    $response->assertRedirect(route('payment.checkout', ['checkout_id' => 'checkout_456']));
});

test('checkout page can be rendered with session data', function () {
    $user = User::factory()->create(['is_active' => true]);

    $response = $this->actingAs($user)
        ->withSession([
            'checkout_amount' => 100.00,
            'checkout_description' => 'Test Payment',
        ])
        ->get('/payment/checkout/test_checkout_id');

    $response->assertSuccessful()
        ->assertSee('€100.00')
        ->assertSee('Test Payment');
});

test('checkout payment process validates card fields', function () {
    $user = User::factory()->create(['is_active' => true]);

    $response = $this->actingAs($user)
        ->post('/payment/checkout/test_checkout_id/process', [
            'card_number' => '',
            'card_name' => '',
            'expiry_month' => '',
            'expiry_year' => '',
            'cvv' => '',
        ]);

    $response->assertSessionHasErrors(['card_number', 'card_name', 'expiry_month', 'expiry_year', 'cvv']);
});

test('failed checkout payment shows error', function () {
    $user = User::factory()->create(['is_active' => true]);

    $sumUpMock = Mockery::mock(SumUpService::class);
    $sumUpMock->shouldReceive('processCheckoutPayment')->andReturn([
        'success' => false,
        'status' => 'FAILED',
        'error' => 'Card declined',
    ]);

    $this->app->instance(SumUpService::class, $sumUpMock);

    $response = $this->actingAs($user)
        ->withSession(['checkout_amount' => 100.00])
        ->post('/payment/checkout/test_checkout_id/process', [
            'card_number' => '4111111111111111',
            'card_name' => 'Test User',
            'expiry_month' => '12',
            'expiry_year' => '2028',
            'cvv' => '123',
        ]);

    $response->assertRedirect(route('payment.checkout', ['checkout_id' => 'test_checkout_id']))
        ->assertSessionHas('error');
});

test('online payment fails gracefully when checkout creation fails', function () {
    $user = User::factory()->create(['is_active' => true]);

    $sumUpMock = Mockery::mock(SumUpService::class);
    $sumUpMock->shouldReceive('createCheckout')->andReturn(null);

    $this->app->instance(SumUpService::class, $sumUpMock);

    $response = $this->actingAs($user)->post('/payment/membership', [
        'payment_method' => 'online',
    ]);

    $response->assertRedirect()
        ->assertSessionHas('error');
});

test('successful checkout payment completes membership payment', function () {
    $user = User::factory()->create(['is_active' => true]);

    $payment = Payment::factory()->create([
        'user_id' => $user->id,
        'payment_type' => PaymentType::Membership,
        'status' => PaymentStatus::Pending,
    ]);

    $sumUpMock = Mockery::mock(SumUpService::class);
    $sumUpMock->shouldReceive('processCheckoutPayment')->andReturn([
        'success' => true,
        'status' => 'PAID',
        'transaction_id' => 'txn_123',
    ]);

    $this->app->instance(SumUpService::class, $sumUpMock);

    $response = $this->actingAs($user)
        ->withSession([
            'checkout_amount' => 100.00,
            'membership_payment_id' => $payment->id,
        ])
        ->post('/payment/checkout/test_checkout_id/process', [
            'card_number' => '4111111111111111',
            'card_name' => 'Test User',
            'expiry_month' => '12',
            'expiry_year' => '2028',
            'cvv' => '123',
        ]);

    $response->assertRedirect(route('dashboard'))
        ->assertSessionHas('success');

    $payment->refresh();
    expect($payment->status)->toBe(PaymentStatus::Completed);

    $user->refresh();
    expect($user->membership)->not->toBeNull();
});

test('successful checkout payment completes credit payment', function () {
    $user = User::factory()->create(['is_active' => true]);

    Membership::create([
        'user_id' => $user->id,
        'start_date' => now(),
        'expiry_date' => now()->addYear(),
        'initial_credits' => 20,
        'purchased_credits' => 0,
        'status' => MembershipStatus::Active,
    ]);

    $payment = Payment::factory()->create([
        'user_id' => $user->id,
        'payment_type' => PaymentType::Credits,
        'amount_cents' => 2500, // 5 credits at €5 each
        'status' => PaymentStatus::Pending,
    ]);

    $sumUpMock = Mockery::mock(SumUpService::class);
    $sumUpMock->shouldReceive('processCheckoutPayment')->andReturn([
        'success' => true,
        'status' => 'PAID',
        'transaction_id' => 'txn_456',
    ]);

    $this->app->instance(SumUpService::class, $sumUpMock);

    $response = $this->actingAs($user)
        ->withSession([
            'checkout_amount' => 25.00,
            'credit_payment_id' => $payment->id,
            'credit_quantity' => 5,
        ])
        ->post('/payment/checkout/test_checkout_id/process', [
            'card_number' => '4111111111111111',
            'card_name' => 'Test User',
            'expiry_month' => '12',
            'expiry_year' => '2028',
            'cvv' => '123',
        ]);

    $response->assertRedirect(route('dashboard'))
        ->assertSessionHas('success');

    $payment->refresh();
    expect($payment->status)->toBe(PaymentStatus::Completed);

    $user->refresh();
    expect($user->membership->purchased_credits)->toBe(5);
});

test('checkout payment clears session data on success', function () {
    $user = User::factory()->create(['is_active' => true]);

    $sumUpMock = Mockery::mock(SumUpService::class);
    $sumUpMock->shouldReceive('processCheckoutPayment')->andReturn([
        'success' => true,
        'status' => 'PAID',
    ]);

    $this->app->instance(SumUpService::class, $sumUpMock);

    $response = $this->actingAs($user)
        ->withSession([
            'checkout_amount' => 100.00,
            'checkout_description' => 'Test',
            'membership_payment_id' => 999,
        ])
        ->post('/payment/checkout/test_checkout_id/process', [
            'card_number' => '4111111111111111',
            'card_name' => 'Test User',
            'expiry_month' => '12',
            'expiry_year' => '2028',
            'cvv' => '123',
        ]);

    $response->assertSessionMissing('checkout_amount')
        ->assertSessionMissing('checkout_description')
        ->assertSessionMissing('membership_payment_id');
});

test('online credit payment fails when checkout creation fails', function () {
    $user = User::factory()->create(['is_active' => true]);

    $sumUpMock = Mockery::mock(SumUpService::class);
    $sumUpMock->shouldReceive('createCheckout')->andReturn(null);

    $this->app->instance(SumUpService::class, $sumUpMock);

    $response = $this->actingAs($user)->post('/payment/credits', [
        'quantity' => 5,
        'payment_method' => 'online',
    ]);

    $response->assertRedirect()
        ->assertSessionHas('error');
});
