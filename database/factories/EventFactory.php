<?php

namespace Database\Factories;

use App\Models\Event;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\Event>
 */
class EventFactory extends Factory
{
    protected $model = Event::class;

    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        $startDate = fake()->dateTimeBetween('+1 week', '+3 months');
        $endDate = (clone $startDate)->modify('+1 day');

        return [
            'title' => fake()->sentence(4),
            'description' => fake()->paragraphs(3, true),
            'start_date' => $startDate,
            'end_date' => fake()->optional(0.5)->dateTimeBetween($startDate, $endDate),
            'location' => fake()->optional(0.8)->address(),
            'capacity' => fake()->optional(0.3)->numberBetween(10, 100),
            'published' => fake()->boolean(70),
        ];
    }

    /**
     * Indicate that the event is published.
     */
    public function published(): static
    {
        return $this->state(fn (array $attributes) => [
            'published' => true,
        ]);
    }

    /**
     * Indicate that the event is unpublished.
     */
    public function unpublished(): static
    {
        return $this->state(fn (array $attributes) => [
            'published' => false,
        ]);
    }
}
