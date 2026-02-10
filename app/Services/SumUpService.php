<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Str;

class SumUpService
{
    private string $apiKey;

    private string $merchantCode;

    private string $baseUrl = 'https://api.sumup.com/v0.1';

    public function __construct()
    {
        $this->apiKey = (string) config('services.sumup.api_key', '');
        $this->merchantCode = (string) config('services.sumup.merchant_code', '');
    }

    /**
     * Create a checkout for payment.
     *
     * @return array<string, mixed>|null
     */
    public function createCheckout(
        int $amountCents,
        string $currency = 'EUR',
        string $description = '',
        ?string $checkoutReference = null,
    ): ?array {
        if (empty($this->apiKey) || empty($this->merchantCode)) {
            Log::error('SumUp API key or merchant code not configured');

            return null;
        }

        $checkoutReference = $checkoutReference ?? (string) Str::uuid();
        $amountEuros = $amountCents / 100.0;

        try {
            $response = Http::withToken($this->apiKey)
                ->post("{$this->baseUrl}/checkouts", [
                    'checkout_reference' => $checkoutReference,
                    'amount' => $amountEuros,
                    'currency' => $currency,
                    'merchant_code' => $this->merchantCode,
                    'description' => $description,
                ]);

            if ($response->successful()) {
                $data = $response->json();
                Log::info('SumUp checkout created', ['id' => $data['id'] ?? 'no id']);

                return [
                    'id' => $data['id'] ?? null,
                    'checkout_reference' => $data['checkout_reference'] ?? $checkoutReference,
                    'status' => $data['status'] ?? 'PENDING',
                ];
            }

            Log::error('SumUp API error creating checkout', [
                'status' => $response->status(),
                'body' => $response->body(),
            ]);

            return null;
        } catch (\Exception $e) {
            Log::error('Error creating SumUp checkout', ['error' => $e->getMessage()]);

            return null;
        }
    }

    /**
     * Get a checkout by ID.
     *
     * @return array<string, mixed>|null
     */
    public function getCheckout(string $checkoutId): ?array
    {
        try {
            $response = Http::withToken($this->apiKey)
                ->get("{$this->baseUrl}/checkouts/{$checkoutId}");

            if ($response->successful()) {
                return $response->json();
            }

            Log::error('SumUp API error getting checkout', [
                'checkout_id' => $checkoutId,
                'status' => $response->status(),
            ]);

            return null;
        } catch (\Exception $e) {
            Log::error('Error getting SumUp checkout', ['error' => $e->getMessage()]);

            return null;
        }
    }

    /**
     * Verify if a payment has been completed.
     */
    public function verifyPayment(string $checkoutId): bool
    {
        $checkout = $this->getCheckout($checkoutId);

        if (! $checkout) {
            return false;
        }

        return ($checkout['status'] ?? '') === 'PAID';
    }

    /**
     * Process a checkout payment with card details.
     *
     * @return array<string, mixed>
     */
    public function processCheckoutPayment(
        string $checkoutId,
        string $cardNumber,
        string $cardName,
        string $expiryMonth,
        string $expiryYear,
        string $cvv,
    ): array {
        try {
            // Format expiry year to 4 digits
            if (strlen($expiryYear) === 2) {
                $expiryYear = '20' . $expiryYear;
            }

            // Format expiry month to 2 digits
            if (strlen($expiryMonth) === 1) {
                $expiryMonth = '0' . $expiryMonth;
            }

            $response = Http::withToken($this->apiKey)
                ->put("{$this->baseUrl}/checkouts/{$checkoutId}", [
                    'payment_type' => 'card',
                    'card' => [
                        'number' => str_replace(' ', '', $cardNumber),
                        'name' => $cardName,
                        'expiry_month' => $expiryMonth,
                        'expiry_year' => $expiryYear,
                        'cvv' => $cvv,
                    ],
                ]);

            $data = $response->json();
            $status = $data['status'] ?? 'FAILED';

            Log::info('SumUp payment processed', [
                'checkout_id' => $checkoutId,
                'status' => $status,
            ]);

            return [
                'success' => $status === 'PAID',
                'status' => $status,
                'checkout_id' => $checkoutId,
                'transaction_id' => $data['transaction_code'] ?? $data['transaction_id'] ?? null,
                'transaction_code' => $data['transaction_code'] ?? null,
            ];
        } catch (\Exception $e) {
            Log::error('Error processing SumUp payment', ['error' => $e->getMessage()]);

            return [
                'success' => false,
                'status' => 'FAILED',
                'error' => $e->getMessage(),
            ];
        }
    }
}
