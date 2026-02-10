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
    Permission::findOrCreate('payments.confirm');
    Permission::findOrCreate('members.read');

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

test('confirming already completed payment shows error', function () {
    Mail::fake();

    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $user = User::factory()->create();
    $service = app(PaymentService::class);
    $payment = $service->createCashMembershipPayment($user);

    // Complete the payment first
    $payment->markCompleted('test');

    $this->actingAs($admin)
        ->post("/admin/payments/{$payment->id}/confirm")
        ->assertRedirect()
        ->assertSessionHas('error', 'Payment is not pending.');
});

test('confirming payment with redirect param returns to custom url', function () {
    Mail::fake();

    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $user = User::factory()->create();
    $service = app(PaymentService::class);
    $payment = $service->createCashMembershipPayment($user);

    // Complete the payment first to trigger error path
    $payment->markCompleted('test');

    $this->actingAs($admin)
        ->post("/admin/payments/{$payment->id}/confirm", [
            'redirect' => route('admin.members.show', $user),
        ])
        ->assertRedirect(route('admin.members.show', $user))
        ->assertSessionHas('error');
});

test('admin can confirm payment from member show page', function () {
    Mail::fake();

    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $user = User::factory()->create();
    $service = app(PaymentService::class);
    $payment = $service->createCashMembershipPayment($user);

    // Confirm with redirect back to member page
    $this->actingAs($admin)
        ->post("/admin/payments/{$payment->id}/confirm", [
            'redirect' => route('admin.members.show', $user),
        ])
        ->assertRedirect(route('admin.members.show', $user))
        ->assertSessionHas('success');

    $payment->refresh();
    expect($payment->status)->toBe(\App\Enums\PaymentStatus::Completed);
});

test('member show page displays confirm button for pending cash payments', function () {
    Mail::fake();

    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $user = User::factory()->create();
    $service = app(PaymentService::class);
    $payment = $service->createCashMembershipPayment($user);

    $this->actingAs($admin)
        ->get(route('admin.members.show', $user))
        ->assertSuccessful()
        ->assertSee('Confirm')
        ->assertSee('Pending');
});
