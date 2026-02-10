<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class () extends Migration {
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('payments', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->integer('amount_cents');
            $table->string('currency', 3)->default('EUR');
            $table->enum('payment_type', ['membership', 'credits']);
            $table->enum('payment_method', ['cash', 'online'])->default('online');
            $table->enum('status', ['pending', 'completed', 'failed', 'cancelled'])->default('pending');
            $table->text('description')->nullable();
            $table->string('payment_processor', 50)->nullable();
            $table->string('external_transaction_id')->unique()->nullable();
            $table->timestamps();

            $table->index('user_id');
            $table->index('status');
            $table->index('external_transaction_id');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('payments');
    }
};
