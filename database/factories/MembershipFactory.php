<?php

namespace Database\Factories;

use App\Enums\MembershipStatus;
use App\Models\Membership;
use App\Models\User;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\Membership>
 */
class MembershipFactory extends Factory
{
    protected $model = Membership::class;

    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        $startDate = now()->subMonths(fake()->numberBetween(0, 6));

        return [
            'user_id' => User::factory(),
            'start_date' => $startDate,
            'expiry_date' => $startDate->copy()->addYear(),
            'initial_credits' => 20,
            'purchased_credits' => fake()->numberBetween(0, 10),
            'status' => MembershipStatus::Active,
        ];
    }

    /**
     * Indicate that the membership is pending.
     */
    public function pending(): static
    {
        return $this->state(fn (array $attributes) => [
            'status' => MembershipStatus::Pending,
        ]);
    }

    /**
     * Indicate that the membership is expired.
     */
    public function expired(): static
    {
        return $this->state(fn (array $attributes) => [
            'expiry_date' => now()->subDays(1),
            'status' => MembershipStatus::Expired,
        ]);
    }
}
