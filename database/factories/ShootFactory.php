<?php

namespace Database\Factories;

use App\Enums\ShootLocation;
use App\Models\Shoot;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\Shoot>
 */
class ShootFactory extends Factory
{
    protected $model = Shoot::class;

    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'date' => fake()->dateTimeBetween('-6 months', '+1 month'),
            'location' => fake()->randomElement(ShootLocation::cases()),
            'description' => fake()->optional(0.5)->sentence(10),
        ];
    }
}
