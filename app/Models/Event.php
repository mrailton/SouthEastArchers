<?php

namespace App\Models;

use Carbon\Carbon;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

/**
 * @property Carbon $start_date
 * @property Carbon|null $end_date
 */
class Event extends Model
{
    use HasFactory;

    protected $fillable = [
        'title',
        'description',
        'start_date',
        'end_date',
        'location',
        'capacity',
        'published',
    ];

    /**
     * @return array<string, string>
     */
    protected function casts(): array
    {
        return [
            'start_date' => 'datetime',
            'end_date' => 'datetime',
            'capacity' => 'integer',
            'published' => 'boolean',
        ];
    }

    public function isUpcoming(): bool
    {
        return $this->start_date->gt(Carbon::now());
    }

    public function publish(): void
    {
        $this->published = true;
    }
}
