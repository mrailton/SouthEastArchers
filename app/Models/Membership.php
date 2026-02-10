<?php

namespace App\Models;

use App\Enums\MembershipStatus;
use App\Settings\ApplicationSettings;
use Carbon\Carbon;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

/**
 * @property MembershipStatus $status
 * @property Carbon $start_date
 * @property Carbon $expiry_date
 */
class Membership extends Model
{
    use HasFactory;

    protected $fillable = [
        'user_id',
        'start_date',
        'expiry_date',
        'initial_credits',
        'purchased_credits',
        'status',
    ];

    /**
     * @return array<string, string>
     */
    protected function casts(): array
    {
        return [
            'start_date' => 'date',
            'expiry_date' => 'date',
            'initial_credits' => 'integer',
            'purchased_credits' => 'integer',
            'status' => MembershipStatus::class,
        ];
    }

    /**
     * @return BelongsTo<User, $this>
     */
    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function isActive(): bool
    {
        return $this->status === MembershipStatus::Active && $this->expiry_date->gte(today());
    }

    public function creditsRemaining(): int
    {
        return ($this->initial_credits ?? 0) + ($this->purchased_credits ?? 0);
    }

    public function useCredit(bool $allowNegative = false): bool
    {
        $initial = $this->initial_credits ?? 0;
        $purchased = $this->purchased_credits ?? 0;
        $totalCredits = $initial + $purchased;

        if ($totalCredits > 0) {
            if ($initial > 0) {
                $this->initial_credits = $initial - 1;
            } else {
                $this->purchased_credits = $purchased - 1;
            }
            $this->save();

            return true;
        } elseif ($allowNegative && $this->isActive()) {
            $this->initial_credits = $initial - 1;
            $this->save();

            return true;
        }

        return false;
    }

    public function addCredits(int $amount): void
    {
        $current = $this->purchased_credits ?? 0;
        $this->purchased_credits = $current + $amount;
        $this->save();
    }

    public function renew(int $initialCredits = 20): void
    {
        $settings = app(ApplicationSettings::class);

        $this->start_date = today();
        $this->expiry_date = $this->calculateExpiryDate($settings);
        $this->initial_credits = $initialCredits;
        $this->status = MembershipStatus::Active;
        $this->save();
    }

    public function activate(): void
    {
        $this->status = MembershipStatus::Active;
        $this->save();
    }

    public function expireInitialCredits(): void
    {
        $this->initial_credits = 0;
    }

    private function calculateExpiryDate(ApplicationSettings $settings): Carbon
    {
        $startMonth = $settings->membership_year_start_month;
        $startDay = $settings->membership_year_start_day;
        $now = today();

        $yearStart = Carbon::create($now->year, $startMonth, $startDay);

        if ($now->lt($yearStart)) {
            $yearStart->subYear();
        }

        return $yearStart->addYear()->subDay();
    }
}
