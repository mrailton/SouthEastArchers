<?php

namespace App\Services;

use App\Enums\PaymentMethod;
use App\Enums\PaymentStatus;
use App\Enums\PaymentType;
use App\Mail\MembershipActivatedMail;
use App\Mail\PaymentReceiptMail;
use App\Models\Payment;
use App\Models\User;
use App\Settings\ApplicationSettings;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Mail;

class PaymentService
{
    public function __construct(
        private SumUpService $sumUpService,
        private ApplicationSettings $settings,
    ) {
    }

    /**
     * Create a checkout for payment.
     *
     * @return array<string, mixed>|null
     */
    public function createCheckout(int $amountCents, string $description): ?array
    {
        return $this->sumUpService->createCheckout($amountCents, 'EUR', $description);
    }

    /**
     * Process a payment with card details.
     *
     * @return array<string, mixed>
     */
    public function processPayment(
        string $checkoutId,
        string $cardNumber,
        string $cardName,
        string $expiryMonth,
        string $expiryYear,
        string $cvv,
    ): array {
        return $this->sumUpService->processCheckoutPayment(
            $checkoutId,
            $cardNumber,
            $cardName,
            $expiryMonth,
            $expiryYear,
            $cvv,
        );
    }

    /**
     * Initiate membership payment via online payment.
     *
     * @return array<string, mixed>
     */
    public function initiateMembershipPayment(User $user): array
    {
        $amountCents = $this->settings->annual_membership_cost;
        $description = "Annual Membership - {$user->name}";

        $payment = Payment::create([
            'user_id' => $user->id,
            'amount_cents' => $amountCents,
            'currency' => 'EUR',
            'payment_type' => PaymentType::Membership,
            'payment_method' => PaymentMethod::Online,
            'description' => $description,
            'status' => PaymentStatus::Pending,
        ]);

        $checkout = $this->createCheckout($amountCents, $description);

        if ($checkout) {
            return [
                'success' => true,
                'checkout_id' => $checkout['id'],
                'payment_id' => $payment->id,
                'amount' => $amountCents / 100.0,
                'description' => $description,
            ];
        }

        $payment->delete();
        Log::error('Failed to create checkout for membership payment', ['user_id' => $user->id]);

        return [
            'success' => false,
            'error' => 'Error creating payment. Please try again.',
        ];
    }

    /**
     * Initiate credit purchase via online payment.
     *
     * @return array<string, mixed>
     */
    public function initiateCreditPurchase(User $user, int $quantity): array
    {
        $amountCents = $quantity * $this->settings->additional_shoot_cost;
        $description = "{$quantity} shooting credits";

        $payment = Payment::create([
            'user_id' => $user->id,
            'amount_cents' => $amountCents,
            'currency' => 'EUR',
            'payment_type' => PaymentType::Credits,
            'payment_method' => PaymentMethod::Online,
            'description' => $description,
            'status' => PaymentStatus::Pending,
        ]);

        $checkout = $this->createCheckout($amountCents, "{$quantity} credits - {$user->name}");

        if ($checkout) {
            return [
                'success' => true,
                'checkout_id' => $checkout['id'],
                'payment_id' => $payment->id,
                'quantity' => $quantity,
                'amount' => $amountCents / 100.0,
                'description' => $description,
            ];
        }

        $payment->delete();
        Log::error('Failed to create checkout for credit purchase', [
            'user_id' => $user->id,
            'quantity' => $quantity,
        ]);

        return [
            'success' => false,
            'error' => 'Error creating payment. Please try again.',
        ];
    }

    /**
     * Create a pending cash payment for membership.
     */
    public function createCashMembershipPayment(User $user): Payment
    {
        $amountCents = $this->settings->annual_membership_cost;

        return Payment::create([
            'user_id' => $user->id,
            'amount_cents' => $amountCents,
            'currency' => 'EUR',
            'payment_type' => PaymentType::Membership,
            'payment_method' => PaymentMethod::Cash,
            'description' => "Annual Membership (Cash) - {$user->name}",
            'status' => PaymentStatus::Pending,
        ]);
    }

    /**
     * Create a pending cash payment for credits.
     */
    public function createCashCreditPayment(User $user, int $quantity): Payment
    {
        $amountCents = $quantity * $this->settings->additional_shoot_cost;

        return Payment::create([
            'user_id' => $user->id,
            'amount_cents' => $amountCents,
            'currency' => 'EUR',
            'payment_type' => PaymentType::Credits,
            'payment_method' => PaymentMethod::Cash,
            'description' => "{$quantity} shooting credits (Cash)",
            'status' => PaymentStatus::Pending,
        ]);
    }

    /**
     * Complete a payment and apply membership/credits.
     */
    public function completePayment(Payment $payment, ?string $transactionId = null): void
    {
        $payment->markCompleted($transactionId, 'sumup');

        $user = $payment->user;

        if ($payment->payment_type === PaymentType::Membership) {
            $this->activateMembership($user);
            $user->refresh();
            if ($user->membership) {
                Mail::to($user)->send(new MembershipActivatedMail($user, $user->membership));
            }
        } elseif ($payment->payment_type === PaymentType::Credits) {
            $this->addCredits($user, $payment);
        }

        Mail::to($user)->send(new PaymentReceiptMail($user, $payment));
    }

    /**
     * Activate or renew membership for a user.
     */
    private function activateMembership(User $user): void
    {
        $membership = $user->membership;

        if ($membership) {
            $membership->renew($this->settings->membership_shoots_included);
        } else {
            $user->membership()->create([
                'start_date' => now(),
                'expiry_date' => $this->calculateExpiryDate(),
                'initial_credits' => $this->settings->membership_shoots_included,
                'purchased_credits' => 0,
                'status' => \App\Enums\MembershipStatus::Active,
            ]);
        }
    }

    /**
     * Add credits to user based on payment.
     */
    private function addCredits(User $user, Payment $payment): void
    {
        // Calculate quantity from payment amount
        $quantity = (int) ($payment->amount_cents / $this->settings->additional_shoot_cost);

        $membership = $user->membership;
        if ($membership) {
            $membership->addCredits($quantity);
        }

        // Create credit record
        $user->credits()->create([
            'amount' => $quantity,
            'payment_id' => $payment->id,
        ]);
    }

    /**
     * Calculate membership expiry date based on settings.
     */
    private function calculateExpiryDate(): \Carbon\Carbon
    {
        $now = now();
        $yearStartMonth = $this->settings->membership_year_start_month;
        $yearStartDay = $this->settings->membership_year_start_day;

        // Create this year's start date
        $thisYearStart = $now->copy()->setMonth($yearStartMonth)->setDay($yearStartDay)->startOfDay();

        // If we're past this year's start, expiry is next year's start
        if ($now->gte($thisYearStart)) {
            return $thisYearStart->addYear();
        }

        // Otherwise, expiry is this year's start
        return $thisYearStart;
    }
}
