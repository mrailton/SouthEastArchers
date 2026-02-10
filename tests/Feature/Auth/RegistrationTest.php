<?php

use App\Mail\WelcomeMail;
use App\Models\User;
use Illuminate\Support\Facades\Mail;

test('registration screen can be rendered', function () {
    $response = $this->get('/register');

    $response->assertSuccessful();
    $response->assertSee('Phone Number');
    $response->assertSee('Qualification');
});

test('new users can register with all required fields', function () {
    Mail::fake();

    $response = $this->post('/register', [
        'name' => 'Test User',
        'email' => 'test@example.com',
        'phone' => '0851234567',
        'password' => 'password',
        'password_confirmation' => 'password',
        'qualification' => 'beginner',
    ]);

    // User should NOT be authenticated (account needs admin approval)
    $this->assertGuest();
    $response->assertRedirect(route('login'));
    $response->assertSessionHas('success');

    // User should be created but inactive
    $user = User::where('email', 'test@example.com')->first();
    expect($user)->not->toBeNull()
        ->and($user->is_active)->toBeFalse()
        ->and($user->phone)->toBe('0851234567')
        ->and($user->qualification)->toBe('beginner');

    Mail::assertQueued(WelcomeMail::class, fn ($mail) => $mail->hasTo('test@example.com'));
});

test('registration requires qualification field', function () {
    $response = $this->post('/register', [
        'name' => 'Test User',
        'email' => 'test@example.com',
        'password' => 'password',
        'password_confirmation' => 'password',
    ]);

    $response->assertSessionHasErrors(['qualification']);
});

test('registration validates qualification values', function () {
    $response = $this->post('/register', [
        'name' => 'Test User',
        'email' => 'test@example.com',
        'password' => 'password',
        'password_confirmation' => 'password',
        'qualification' => 'invalid',
    ]);

    $response->assertSessionHasErrors(['qualification']);
});

test('phone field is optional during registration', function () {
    Mail::fake();

    $response = $this->post('/register', [
        'name' => 'Test User',
        'email' => 'testnodeneme@example.com',
        'password' => 'password',
        'password_confirmation' => 'password',
        'qualification' => 'none',
    ]);

    $response->assertRedirect(route('login'));
    expect(User::where('email', 'testnodeneme@example.com')->exists())->toBeTrue();
});
