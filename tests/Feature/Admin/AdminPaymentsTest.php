<?php

use App\Enums\MembershipStatus;
use App\Models\Membership;
use App\Models\User;
use App\Services\PaymentService;
use Illuminate\Support\Facades\Mail;
use Spatie\Permission\Models\Permission;
use Spatie\Permission\Models\Role;

beforeEach(function () {
    Permission::findOrCreate('admin.dashboard.view');
    Permission::findOrCreate('payments.manage');

    $adminRole = Role::findOrCreate('Admin');
    $adminRole->givePermissionTo(Permission::all());
});

test('pending cash payments page shows pending payments', function () {
    Mail::fake();

    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $user = User::factory()->create();
    $service = app(PaymentService::class);
    $payment = $service->createCashMembershipPayment($user);

    $this->actingAs($admin)
        ->get('/admin/payments/pending')
        ->assertSuccessful()
        ->assertSee('Pending');
});

test('admin can confirm cash payment', function () {
    Mail::fake();

    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $user = User::factory()->create();
    $service = app(PaymentService::class);
    $payment = $service->createCashMembershipPayment($user);

    $this->actingAs($admin)
        ->post("/admin/payments/{$payment->id}/confirm")
        ->assertRedirect();

    $payment->refresh();
    expect($payment->status)->toBe(\App\Enums\PaymentStatus::Completed);
});

test('confirming membership payment activates membership', function () {
    Mail::fake();

    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $user = User::factory()->create();
    $service = app(PaymentService::class);
    $payment = $service->createCashMembershipPayment($user);

    $this->actingAs($admin)
        ->post("/admin/payments/{$payment->id}/confirm");

    $user->refresh();
    expect($user->membership)->not->toBeNull()
        ->and($user->membership->status)->toBe(MembershipStatus::Active);
});

test('confirming credit payment adds credits', function () {
    Mail::fake();

    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $user = User::factory()->create();

    // Create membership first
    Membership::create([
        'user_id' => $user->id,
        'start_date' => now(),
        'expiry_date' => now()->addYear(),
        'initial_credits' => 20,
        'purchased_credits' => 0,
        'status' => MembershipStatus::Active,
    ]);

    $service = app(PaymentService::class);
    $payment = $service->createCashCreditPayment($user, 5);

    $this->actingAs($admin)
        ->post("/admin/payments/{$payment->id}/confirm");

    $user->refresh();
    expect($user->membership->purchased_credits)->toBe(5);
});
