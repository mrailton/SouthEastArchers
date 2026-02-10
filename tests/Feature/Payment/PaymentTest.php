<?php

use App\Enums\PaymentMethod;
use App\Enums\PaymentStatus;
use App\Enums\PaymentType;
use App\Models\Payment;
use App\Models\User;

test('membership payment page requires authentication', function () {
    $this->get('/payment/membership')->assertRedirect('/login');
});

test('membership payment page can be rendered', function () {
    $user = User::factory()->create(['is_active' => true]);

    $this->actingAs($user)
        ->get('/payment/membership')
        ->assertSuccessful();
});

test('credits purchase page can be rendered', function () {
    $user = User::factory()->create(['is_active' => true]);

    $this->actingAs($user)
        ->get('/payment/credits')
        ->assertSuccessful();
});

test('cash membership payment creates pending payment', function () {
    $user = User::factory()->create(['is_active' => true]);

    $response = $this->actingAs($user)->post('/payment/membership', [
        'payment_method' => 'cash',
    ]);

    $response->assertRedirect(route('dashboard'));

    $payment = Payment::where('user_id', $user->id)->first();
    expect($payment)->not->toBeNull()
        ->and($payment->payment_method)->toBe(PaymentMethod::Cash)
        ->and($payment->payment_type)->toBe(PaymentType::Membership)
        ->and($payment->status)->toBe(PaymentStatus::Pending);
});

test('cash credit payment creates pending payment', function () {
    $user = User::factory()->create(['is_active' => true]);

    $response = $this->actingAs($user)->post('/payment/credits', [
        'quantity' => 5,
        'payment_method' => 'cash',
    ]);

    $response->assertRedirect(route('credits'));

    $payment = Payment::where('user_id', $user->id)->first();
    expect($payment)->not->toBeNull()
        ->and($payment->payment_method)->toBe(PaymentMethod::Cash)
        ->and($payment->payment_type)->toBe(PaymentType::Credits)
        ->and($payment->status)->toBe(PaymentStatus::Pending);
});

test('payment history page can be rendered', function () {
    $user = User::factory()->create(['is_active' => true]);

    Payment::factory()->create([
        'user_id' => $user->id,
        'status' => PaymentStatus::Completed,
    ]);

    $this->actingAs($user)
        ->get('/payment/history')
        ->assertSuccessful();
});

test('payment history shows user payments', function () {
    $user = User::factory()->create(['is_active' => true]);

    Payment::factory()->create([
        'user_id' => $user->id,
        'status' => PaymentStatus::Completed,
    ]);

    $this->actingAs($user)
        ->get('/payment/history')
        ->assertSuccessful()
        ->assertSee('Completed');
});

test('credits quantity validation', function () {
    $user = User::factory()->create(['is_active' => true]);

    $response = $this->actingAs($user)->post('/payment/credits', [
        'quantity' => 0,
        'payment_method' => 'cash',
    ]);

    $response->assertSessionHasErrors(['quantity']);
});
