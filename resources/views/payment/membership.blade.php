<x-app-layout>
    <x-slot name="title">Membership Payment</x-slot>

    <div class="max-w-2xl mx-auto">
        <h1 class="text-4xl font-bold mb-6">Annual Membership Payment</h1>

        @if (session('error'))
            <div class="alert-error mb-4">
                {{ session('error') }}
            </div>
        @endif

        <div class="card p-8 mb-6">
            <h2 class="text-2xl font-bold mb-4">What You Get</h2>
            <ul class="space-y-2 mb-6">
                <li class="flex items-center">
                    <span class="text-green-600 mr-2">✓</span>
                    <span>{{ $shootsIncluded }} shoots per year</span>
                </li>
                <li class="flex items-center">
                    <span class="text-green-600 mr-2">✓</span>
                    <span>Access to member portal</span>
                </li>
                <li class="flex items-center">
                    <span class="text-green-600 mr-2">✓</span>
                    <span>Community events and training</span>
                </li>
                <li class="flex items-center">
                    <span class="text-green-600 mr-2">✓</span>
                    <span>Purchase additional credits as needed</span>
                </li>
            </ul>

            <div class="text-3xl font-bold text-[--sea-primary] mb-6">€{{ number_format($annualCost, 2) }}</div>

            <form method="POST" action="{{ route('payment.membership') }}" class="space-y-4">
                @csrf

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

        <div class="bg-gray-100 p-6 rounded">
            <h3 class="font-bold mb-2">Payment Information</h3>
            <p class="text-gray-700 text-sm">
                Online payments are processed securely through SumUp. No credit card information is stored on our
                servers.
                For cash payments, please bring the exact amount to the next shoot and an admin will confirm your
                payment.
            </p>
        </div>
    </div>
</x-app-layout>
