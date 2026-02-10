<?php

use App\Enums\MembershipStatus;
use App\Enums\PaymentMethod;
use App\Enums\PaymentStatus;
use App\Enums\PaymentType;
use App\Enums\ShootLocation;

test('membership status enum has correct values', function () {
    expect(MembershipStatus::Pending->value)->toBe('pending')
        ->and(MembershipStatus::Active->value)->toBe('active')
        ->and(MembershipStatus::Expired->value)->toBe('expired')
        ->and(MembershipStatus::Cancelled->value)->toBe('cancelled');
});

test('payment method enum has correct values', function () {
    expect(PaymentMethod::Online->value)->toBe('online')
        ->and(PaymentMethod::Cash->value)->toBe('cash');
});

test('payment status enum has correct values', function () {
    expect(PaymentStatus::Pending->value)->toBe('pending')
        ->and(PaymentStatus::Completed->value)->toBe('completed')
        ->and(PaymentStatus::Failed->value)->toBe('failed')
        ->and(PaymentStatus::Cancelled->value)->toBe('cancelled');
});

test('payment type enum has correct values', function () {
    expect(PaymentType::Membership->value)->toBe('membership')
        ->and(PaymentType::Credits->value)->toBe('credits');
});

test('shoot location enum has correct values', function () {
    expect(ShootLocation::Hall->value)->toBe('Hall')
        ->and(ShootLocation::Meadow->value)->toBe('Meadow')
        ->and(ShootLocation::Woods->value)->toBe('Woods');
});
