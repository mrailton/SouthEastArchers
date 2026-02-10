<?php

use App\Models\User;
use Illuminate\Auth\Events\Verified;
use Illuminate\Support\Facades\Event;
use Illuminate\Support\Facades\URL;

test('email verification screen can be rendered', function () {
    $user = User::factory()->unverified()->create(['is_active' => true]);

    $response = $this->actingAs($user)->get('/verify-email');

    $response->assertStatus(200);
});

test('email verification screen redirects if already verified', function () {
    $user = User::factory()->create(['is_active' => true]);

    $response = $this->actingAs($user)->get('/verify-email');

    $response->assertRedirect(route('dashboard'));
});

test('email can be verified', function () {
    $user = User::factory()->unverified()->create(['is_active' => true]);

    Event::fake();

    $verificationUrl = URL::temporarySignedRoute(
        'verification.verify',
        now()->addMinutes(60),
        ['id' => $user->id, 'hash' => sha1($user->email)],
    );

    $response = $this->actingAs($user)->get($verificationUrl);

    Event::assertDispatched(Verified::class);
    expect($user->fresh()->hasVerifiedEmail())->toBeTrue();
    $response->assertRedirect(route('dashboard', absolute: false) . '?verified=1');
});

test('already verified email redirects without event', function () {
    $user = User::factory()->create(['is_active' => true]);

    Event::fake();

    $verificationUrl = URL::temporarySignedRoute(
        'verification.verify',
        now()->addMinutes(60),
        ['id' => $user->id, 'hash' => sha1($user->email)],
    );

    $response = $this->actingAs($user)->get($verificationUrl);

    Event::assertNotDispatched(Verified::class);
    $response->assertRedirect(route('dashboard', absolute: false) . '?verified=1');
});

test('email is not verified with invalid hash', function () {
    $user = User::factory()->unverified()->create(['is_active' => true]);

    $verificationUrl = URL::temporarySignedRoute(
        'verification.verify',
        now()->addMinutes(60),
        ['id' => $user->id, 'hash' => sha1('wrong-email')],
    );

    $this->actingAs($user)->get($verificationUrl);

    expect($user->fresh()->hasVerifiedEmail())->toBeFalse();
});

test('verification notification can be resent', function () {
    $user = User::factory()->unverified()->create(['is_active' => true]);

    $response = $this->actingAs($user)->post('/email/verification-notification');

    $response->assertSessionHas('status', 'verification-link-sent');
});

test('verification notification redirects if already verified', function () {
    $user = User::factory()->create(['is_active' => true]);

    $response = $this->actingAs($user)->post('/email/verification-notification');

    $response->assertRedirect(route('dashboard'));
});
