<?php

namespace Database\Factories;

use App\Enums\PaymentMethod;
use App\Enums\PaymentStatus;
use App\Enums\PaymentType;
use App\Models\Payment;
use App\Models\User;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\Payment>
 */
class PaymentFactory extends Factory
{
    protected $model = Payment::class;

    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        $paymentType = fake()->randomElement(PaymentType::cases());
        $amountCents = $paymentType === PaymentType::Membership ? 10000 : fake()->numberBetween(1, 10) * 500;

        return [
            'user_id' => User::factory(),
            'amount_cents' => $amountCents,
            'currency' => 'EUR',
            'payment_type' => $paymentType,
            'payment_method' => fake()->randomElement(PaymentMethod::cases()),
            'status' => PaymentStatus::Completed,
            'description' => $paymentType === PaymentType::Membership
                ? 'Annual Membership'
                : fake()->numberBetween(1, 10) . ' shooting credits',
            'payment_processor' => 'sumup',
            'external_transaction_id' => fake()->optional(0.8)->uuid(),
        ];
    }

    /**
     * Indicate that the payment is pending.
     */
    public function pending(): static
    {
        return $this->state(fn (array $attributes) => [
            'status' => PaymentStatus::Pending,
            'external_transaction_id' => null,
        ]);
    }

    /**
     * Indicate that the payment is for membership.
     */
    public function membership(): static
    {
        return $this->state(fn (array $attributes) => [
            'payment_type' => PaymentType::Membership,
            'amount_cents' => 10000,
            'description' => 'Annual Membership',
        ]);
    }

    /**
     * Indicate that the payment is for credits.
     */
    public function credits(int $quantity = 5): static
    {
        return $this->state(fn (array $attributes) => [
            'payment_type' => PaymentType::Credits,
            'amount_cents' => $quantity * 500,
            'description' => $quantity . ' shooting credits',
        ]);
    }

    /**
     * Indicate that the payment is cash.
     */
    public function cash(): static
    {
        return $this->state(fn (array $attributes) => [
            'payment_method' => PaymentMethod::Cash,
            'payment_processor' => null,
            'external_transaction_id' => null,
        ]);
    }
}
