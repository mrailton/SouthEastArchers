<x-app-layout>
    <x-slot name="title">Purchase Credits</x-slot>

    <div class="max-w-2xl mx-auto">
        <h1 class="text-4xl font-bold mb-6">Purchase Additional Credits</h1>

        @if (session('error'))
            <div class="alert-error mb-4">
                {{ session('error') }}
            </div>
        @endif

        @if (session('success'))
            <div class="alert-success mb-4">
                {{ session('success') }}
            </div>
        @endif

        <div class="card p-8 mb-6">
            <h2 class="text-2xl font-bold mb-4">€{{ number_format($creditCost, 2) }} per shoot</h2>
            <p class="text-gray-700 mb-6">Purchase additional credits to attend extra shoots beyond your annual
                membership.</p>

            <form method="POST" action="{{ route('payment.credits') }}" class="space-y-6">
                @csrf

                <div>
                    <label class="block text-gray-700 font-bold mb-2">Number of Credits</label>
                    <select name="quantity"
                        class="w-full border border-gray-300 rounded px-3 py-2 text-lg focus:outline-none focus:ring-2 focus:ring-[--sea-primary]">
                        <option value="1">1 credit - €{{ number_format($creditCost * 1, 2) }}</option>
                        <option value="5">5 credits - €{{ number_format($creditCost * 5, 2) }}</option>
                        <option value="10">10 credits - €{{ number_format($creditCost * 10, 2) }}</option>
                        <option value="20">20 credits - €{{ number_format($creditCost * 20, 2) }}</option>
                        <option value="50">50 credits - €{{ number_format($creditCost * 50, 2) }}</option>
                    </select>
                    @error('quantity')
                        <p class="text-red-600 text-sm mt-1">{{ $message }}</p>
                    @enderror
                </div>

                <div>
                    <label class="block text-gray-700 font-bold mb-2">Payment Method</label>
                    <div class="space-y-2">
                        <label class="flex items-center">
                            <input type="radio" name="payment_method" value="online" checked
                                class="mr-2 text-[--sea-primary]">
                            <span>Pay Online (Card)</span>
                        </label>
                        <label class="flex items-center">
                            <input type="radio" name="payment_method" value="cash" class="mr-2 text-[--sea-primary]">
                            <span>Pay Cash (Requires admin confirmation)</span>
                        </label>
                    </div>
                </div>

                <button type="submit" class="btn-primary w-full py-3">
                    Proceed to Payment
                </button>
            </form>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-gray-100 p-6 rounded">
                <h3 class="font-bold mb-2">Your Current Credits</h3>
                <p class="text-gray-700 text-sm">
                    Check your <a href="{{ route('credits') }}" class="text-[--sea-primary] hover:underline">credits
                        page</a> to view your current credit balance.
                </p>
            </div>

            <div class="bg-gray-100 p-6 rounded">
                <h3 class="font-bold mb-2">Secure Payment</h3>
                <p class="text-gray-700 text-sm">
                    Payments are processed securely through SumUp. No credit card information is stored on our servers.
                </p>
            </div>
        </div>
    </div>
</x-app-layout>
