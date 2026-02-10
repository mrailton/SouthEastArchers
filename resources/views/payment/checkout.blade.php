<x-app-layout>
    <x-slot name="title">Complete Payment</x-slot>

    <div class="max-w-2xl mx-auto">
        <div class="card p-8">
            <h2 class="text-3xl font-bold mb-6 text-center">Complete Payment</h2>

            @if (session('error'))
                <div class="alert-error mb-4">
                    {{ session('error') }}
                </div>
            @endif

            <!-- Payment Summary -->
            <div class="bg-gray-50 p-4 rounded mb-6">
                <h3 class="font-semibold mb-2">Payment Summary</h3>
                <div class="flex justify-between mb-1">
                    <span>{{ $description }}</span>
                    <span class="font-bold">€{{ number_format($amount, 2) }}</span>
                </div>
            </div>

            <!-- Payment Form -->
            <form method="POST" action="{{ route('payment.checkout.process', ['checkout_id' => $checkoutId]) }}"
                class="space-y-4">
                @csrf

                <!-- Card Number -->
                <div>
                    <label class="block text-gray-700 font-bold mb-2">Card Number *</label>
                    <input type="text" name="card_number" placeholder="1234 5678 9012 3456" maxlength="19"
                        class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[--sea-primary]"
                        required pattern="[0-9\s]{13,19}" autocomplete="cc-number" x-data
                        x-on:input="$el.value = $el.value.replace(/\s/g, '').match(/.{1,4}/g)?.join(' ') || $el.value">
                    @error('card_number')
                        <p class="text-red-600 text-sm mt-1">{{ $message }}</p>
                    @enderror
                </div>

                <!-- Cardholder Name -->
                <div>
                    <label class="block text-gray-700 font-bold mb-2">Cardholder Name *</label>
                    <input type="text" name="card_name" placeholder="John Doe"
                        class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[--sea-primary]"
                        required autocomplete="cc-name">
                    @error('card_name')
                        <p class="text-red-600 text-sm mt-1">{{ $message }}</p>
                    @enderror
                </div>

                <!-- Expiry and CVV -->
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-gray-700 font-bold mb-2">Expiry Month *</label>
                        <select name="expiry_month"
                            class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[--sea-primary]"
                            required autocomplete="cc-exp-month">
                            <option value="">Month</option>
                            <option value="01">01 - January</option>
                            <option value="02">02 - February</option>
                            <option value="03">03 - March</option>
                            <option value="04">04 - April</option>
                            <option value="05">05 - May</option>
                            <option value="06">06 - June</option>
                            <option value="07">07 - July</option>
                            <option value="08">08 - August</option>
                            <option value="09">09 - September</option>
                            <option value="10">10 - October</option>
                            <option value="11">11 - November</option>
                            <option value="12">12 - December</option>
                        </select>
                        @error('expiry_month')
                            <p class="text-red-600 text-sm mt-1">{{ $message }}</p>
                        @enderror
                    </div>

                    <div>
                        <label class="block text-gray-700 font-bold mb-2">Expiry Year *</label>
                        <select name="expiry_year"
                            class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[--sea-primary]"
                            required autocomplete="cc-exp-year">
                            <option value="">Year</option>
                            @for ($year = date('Y'); $year <= date('Y') + 10; $year++)
                                <option value="{{ $year }}">{{ $year }}</option>
                            @endfor
                        </select>
                        @error('expiry_year')
                            <p class="text-red-600 text-sm mt-1">{{ $message }}</p>
                        @enderror
                    </div>
                </div>

                <!-- CVV -->
                <div>
                    <label class="block text-gray-700 font-bold mb-2">CVV/CVC *</label>
                    <input type="text" name="cvv" placeholder="123" maxlength="4" pattern="[0-9]{3,4}"
                        class="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[--sea-primary]"
                        required autocomplete="cc-csc">
                    <p class="text-sm text-gray-500 mt-1">3 or 4 digit security code on the back of your card</p>
                    @error('cvv')
                        <p class="text-red-600 text-sm mt-1">{{ $message }}</p>
                    @enderror
                </div>

                <!-- Security Notice -->
                <div class="bg-blue-50 border-l-4 border-blue-400 p-4 my-4">
                    <div class="flex">
                        <div class="flex-shrink-0">
                            <svg class="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd"
                                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                                    clip-rule="evenodd" />
                            </svg>
                        </div>
                        <div class="ml-3">
                            <p class="text-sm text-blue-700">
                                Your payment is processed securely by SumUp. We never store your card details.
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Submit Button -->
                <button type="submit" class="btn-primary w-full py-3">
                    Pay €{{ number_format($amount, 2) }}
                </button>

                <!-- Cancel Link -->
                <div class="text-center mt-4">
                    <a href="{{ route('dashboard') }}" class="text-gray-600 hover:text-gray-800">
                        Cancel and return to dashboard
                    </a>
                </div>
            </form>

            <!-- Accepted Cards -->
            <div class="mt-6 text-center text-gray-500 text-sm">
                <p class="mb-2">Accepted payment methods:</p>
                <div class="flex justify-center space-x-4">
                    <span>💳 Visa</span>
                    <span>💳 Mastercard</span>
                    <span>💳 Amex</span>
                </div>
            </div>
        </div>
    </div>
</x-app-layout>
