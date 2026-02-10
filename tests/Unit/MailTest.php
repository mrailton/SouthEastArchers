<?php

use App\Mail\AccountActivatedMail;
use App\Mail\MembershipActivatedMail;
use App\Mail\PaymentReceiptMail;
use App\Mail\WelcomeMail;
use App\Models\Membership;
use App\Models\Payment;
use App\Models\User;

test('welcome mail has correct subject', function () {
    $user = User::factory()->create();
    $mail = new WelcomeMail($user);

    expect($mail->envelope()->subject)->toBe('Welcome to South East Archers');
});

test('welcome mail has correct view', function () {
    $user = User::factory()->create();
    $mail = new WelcomeMail($user);

    expect($mail->content()->view)->toBe('emails.welcome');
});

test('account activated mail has correct subject', function () {
    $user = User::factory()->create();
    $mail = new AccountActivatedMail($user);

    expect($mail->envelope()->subject)->toBe('Your Account Has Been Activated - South East Archers');
});

test('account activated mail has correct view', function () {
    $user = User::factory()->create();
    $mail = new AccountActivatedMail($user);

    expect($mail->content()->view)->toBe('emails.account-activated');
});

test('payment receipt mail has correct subject', function () {
    $user = User::factory()->create();
    $payment = Payment::factory()->create(['user_id' => $user->id]);
    $mail = new PaymentReceiptMail($user, $payment);

    expect($mail->envelope()->subject)->toBe('Payment Receipt - South East Archers');
});

test('payment receipt mail has correct view', function () {
    $user = User::factory()->create();
    $payment = Payment::factory()->create(['user_id' => $user->id]);
    $mail = new PaymentReceiptMail($user, $payment);

    expect($mail->content()->view)->toBe('emails.payment-receipt');
});

test('membership activated mail has correct subject', function () {
    $user = User::factory()->create();
    $membership = Membership::factory()->create(['user_id' => $user->id]);
    $mail = new MembershipActivatedMail($user, $membership);

    expect($mail->envelope()->subject)->toBe('Your Membership is Now Active - South East Archers');
});

test('membership activated mail has correct view', function () {
    $user = User::factory()->create();
    $membership = Membership::factory()->create(['user_id' => $user->id]);
    $mail = new MembershipActivatedMail($user, $membership);

    expect($mail->content()->view)->toBe('emails.membership-activated');
});

test('all mails have no attachments', function () {
    $user = User::factory()->create();
    $payment = Payment::factory()->create(['user_id' => $user->id]);
    $membership = Membership::factory()->create(['user_id' => $user->id]);

    expect((new WelcomeMail($user))->attachments())->toBeEmpty()
        ->and((new AccountActivatedMail($user))->attachments())->toBeEmpty()
        ->and((new PaymentReceiptMail($user, $payment))->attachments())->toBeEmpty()
        ->and((new MembershipActivatedMail($user, $membership))->attachments())->toBeEmpty();
});
