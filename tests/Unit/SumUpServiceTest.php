<?php

use App\Services\SumUpService;
use Illuminate\Support\Facades\Http;

test('sumup service creates checkout successfully', function () {
    Http::fake([
        'api.sumup.com/*' => Http::response([
            'id' => 'checkout_123',
            'checkout_reference' => 'ref_123',
            'status' => 'PENDING',
        ], 200),
    ]);

    config(['services.sumup.api_key' => 'test_api_key']);
    config(['services.sumup.merchant_code' => 'test_merchant']);

    $service = new SumUpService();
    $result = $service->createCheckout(10000, 'EUR', 'Test Payment');

    expect($result)->toBeArray()
        ->and($result['id'])->toBe('checkout_123')
        ->and($result['status'])->toBe('PENDING');
});

test('sumup service returns null when api call fails', function () {
    Http::fake([
        'api.sumup.com/*' => Http::response(['error' => 'Unauthorized'], 401),
    ]);

    config(['services.sumup.api_key' => 'test_api_key']);
    config(['services.sumup.merchant_code' => 'test_merchant']);

    $service = new SumUpService();
    $result = $service->createCheckout(10000, 'EUR', 'Test Payment');

    expect($result)->toBeNull();
});

test('sumup service returns null when not configured', function () {
    config(['services.sumup.api_key' => '']);
    config(['services.sumup.merchant_code' => '']);

    $service = new SumUpService();
    $result = $service->createCheckout(10000, 'EUR', 'Test Payment');

    expect($result)->toBeNull();
});

test('sumup service gets checkout', function () {
    Http::fake([
        'api.sumup.com/*' => Http::response([
            'id' => 'checkout_123',
            'status' => 'PAID',
        ], 200),
    ]);

    config(['services.sumup.api_key' => 'test_api_key']);
    config(['services.sumup.merchant_code' => 'test_merchant']);

    $service = new SumUpService();
    $result = $service->getCheckout('checkout_123');

    expect($result)->toBeArray()
        ->and($result['status'])->toBe('PAID');
});

test('sumup service returns null when get checkout fails', function () {
    Http::fake([
        'api.sumup.com/*' => Http::response(['error' => 'Not found'], 404),
    ]);

    config(['services.sumup.api_key' => 'test_api_key']);
    config(['services.sumup.merchant_code' => 'test_merchant']);

    $service = new SumUpService();
    $result = $service->getCheckout('invalid_checkout');

    expect($result)->toBeNull();
});

test('sumup service verifies paid payment', function () {
    Http::fake([
        'api.sumup.com/*' => Http::response([
            'id' => 'checkout_123',
            'status' => 'PAID',
        ], 200),
    ]);

    config(['services.sumup.api_key' => 'test_api_key']);
    config(['services.sumup.merchant_code' => 'test_merchant']);

    $service = new SumUpService();
    $result = $service->verifyPayment('checkout_123');

    expect($result)->toBeTrue();
});

test('sumup service verifies unpaid payment as false', function () {
    Http::fake([
        'api.sumup.com/*' => Http::response([
            'id' => 'checkout_123',
            'status' => 'PENDING',
        ], 200),
    ]);

    config(['services.sumup.api_key' => 'test_api_key']);
    config(['services.sumup.merchant_code' => 'test_merchant']);

    $service = new SumUpService();
    $result = $service->verifyPayment('checkout_123');

    expect($result)->toBeFalse();
});

test('sumup service processes payment successfully', function () {
    Http::fake([
        'api.sumup.com/*' => Http::response([
            'id' => 'checkout_123',
            'status' => 'PAID',
            'transaction_code' => 'txn_abc123',
        ], 200),
    ]);

    config(['services.sumup.api_key' => 'test_api_key']);
    config(['services.sumup.merchant_code' => 'test_merchant']);

    $service = new SumUpService();
    $result = $service->processCheckoutPayment(
        'checkout_123',
        '4111111111111111',
        'Test User',
        '12',
        '2028',
        '123',
    );

    expect($result['success'])->toBeTrue()
        ->and($result['status'])->toBe('PAID')
        ->and($result['transaction_code'])->toBe('txn_abc123');
});

test('sumup service formats single digit expiry month', function () {
    Http::fake([
        'api.sumup.com/*' => Http::response([
            'status' => 'PAID',
        ], 200),
    ]);

    config(['services.sumup.api_key' => 'test_api_key']);
    config(['services.sumup.merchant_code' => 'test_merchant']);

    $service = new SumUpService();
    $result = $service->processCheckoutPayment(
        'checkout_123',
        '4111111111111111',
        'Test User',
        '1',  // Single digit month - should be padded to "01"
        '2028',
        '123',
    );

    expect($result['success'])->toBeTrue();
});

test('sumup service formats two digit expiry year', function () {
    Http::fake([
        'api.sumup.com/*' => Http::response([
            'status' => 'PAID',
        ], 200),
    ]);

    config(['services.sumup.api_key' => 'test_api_key']);
    config(['services.sumup.merchant_code' => 'test_merchant']);

    $service = new SumUpService();
    $result = $service->processCheckoutPayment(
        'checkout_123',
        '4111111111111111',
        'Test User',
        '12',
        '28',  // Two digit year - should be converted to "2028"
        '123',
    );

    expect($result['success'])->toBeTrue();
});

test('sumup service handles failed payment', function () {
    Http::fake([
        'api.sumup.com/*' => Http::response([
            'status' => 'FAILED',
        ], 200),
    ]);

    config(['services.sumup.api_key' => 'test_api_key']);
    config(['services.sumup.merchant_code' => 'test_merchant']);

    $service = new SumUpService();
    $result = $service->processCheckoutPayment(
        'checkout_123',
        '4111111111111111',
        'Test User',
        '12',
        '2028',
        '123',
    );

    expect($result['success'])->toBeFalse()
        ->and($result['status'])->toBe('FAILED');
});

test('sumup service handles exception during checkout creation', function () {
    Http::fake([
        'api.sumup.com/*' => fn () => throw new \Exception('Connection error'),
    ]);

    config(['services.sumup.api_key' => 'test_api_key']);
    config(['services.sumup.merchant_code' => 'test_merchant']);

    $service = new SumUpService();
    $result = $service->createCheckout(10000, 'EUR', 'Test Payment');

    expect($result)->toBeNull();
});

test('sumup service handles exception during get checkout', function () {
    Http::fake([
        'api.sumup.com/*' => fn () => throw new \Exception('Connection error'),
    ]);

    config(['services.sumup.api_key' => 'test_api_key']);
    config(['services.sumup.merchant_code' => 'test_merchant']);

    $service = new SumUpService();
    $result = $service->getCheckout('checkout_123');

    expect($result)->toBeNull();
});

test('sumup service returns false when verify payment gets null checkout', function () {
    Http::fake([
        'api.sumup.com/*' => fn () => throw new \Exception('Connection error'),
    ]);

    config(['services.sumup.api_key' => 'test_api_key']);
    config(['services.sumup.merchant_code' => 'test_merchant']);

    $service = new SumUpService();
    $result = $service->verifyPayment('checkout_123');

    expect($result)->toBeFalse();
});

test('sumup service handles exception during payment processing', function () {
    Http::fake([
        'api.sumup.com/*' => fn () => throw new \Exception('Connection error'),
    ]);

    config(['services.sumup.api_key' => 'test_api_key']);
    config(['services.sumup.merchant_code' => 'test_merchant']);

    $service = new SumUpService();
    $result = $service->processCheckoutPayment(
        'checkout_123',
        '4111111111111111',
        'Test User',
        '12',
        '2028',
        '123',
    );

    expect($result['success'])->toBeFalse()
        ->and($result['status'])->toBe('FAILED')
        ->and($result['error'])->toBe('Connection error');
});
