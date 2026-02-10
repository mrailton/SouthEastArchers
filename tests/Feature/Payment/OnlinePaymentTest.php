<?php

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
