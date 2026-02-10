<?php

namespace App\Models;

use App\Enums\PaymentMethod;
use App\Enums\PaymentStatus;
use App\Enums\PaymentType;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

/**
 * @property PaymentStatus $status
 * @property PaymentType $payment_type
 * @property PaymentMethod $payment_method
 */
class Payment extends Model
{
    use HasFactory;

    protected $fillable = [
        'user_id',
        'amount_cents',
        'currency',
        'payment_type',
        'payment_method',
        'status',
        'description',
        'payment_processor',
        'external_transaction_id',
    ];

    /**
     * @return array<string, string>
     */
    protected function casts(): array
    {
        return [
            'amount_cents' => 'integer',
            'payment_type' => PaymentType::class,
            'payment_method' => PaymentMethod::class,
            'status' => PaymentStatus::class,
        ];
    }

    /**
     * @return BelongsTo<User, $this>
     */
    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    /**
     * @return HasMany<Credit, $this>
     */
    public function credits(): HasMany
    {
        return $this->hasMany(Credit::class);
    }

    public function markCompleted(?string $transactionId = null, ?string $processor = null): void
    {
        $this->status = PaymentStatus::Completed;
        $this->external_transaction_id = $transactionId;
        $this->payment_processor = $processor;
        $this->save();
    }

    public function markFailed(): void
    {
        $this->status = PaymentStatus::Failed;
        $this->save();
    }

    public function getAmountAttribute(): float
    {
        return $this->amount_cents / 100.0;
    }

    public function setAmountAttribute(float $value): void
    {
        $this->amount_cents = (int) round($value * 100);
    }
}
