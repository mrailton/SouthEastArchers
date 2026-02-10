<?php

use App\Models\User;
use Illuminate\Support\Facades\RateLimiter;

test('login is throttled after too many attempts', function () {
    $user = User::factory()->create(['is_active' => true]);

    // Make 5 failed attempts
    for ($i = 0; $i < 5; $i++) {
        $this->post('/login', [
            'email' => $user->email,
            'password' => 'wrong-password',
        ]);
    }

    // 6th attempt should be throttled
    $response = $this->post('/login', [
        'email' => $user->email,
        'password' => 'wrong-password',
    ]);

    $response->assertSessionHasErrors('email');
    expect(session('errors')->get('email')[0])->toContain('Too many login attempts');
});

test('throttle key is based on email and ip', function () {
    RateLimiter::clear('test@example.com|127.0.0.1');

    $user = User::factory()->create([
        'email' => 'test@example.com',
        'is_active' => true,
    ]);

    // First attempt should work (not throttled)
    $response = $this->post('/login', [
        'email' => $user->email,
        'password' => 'wrong-password',
    ]);

    $response->assertSessionHasErrors('email');
    // Should be a normal auth error, not throttle error
    expect(session('errors')->get('email')[0])->not->toContain('Too many');
});
