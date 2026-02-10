<x-app-layout>
    <x-slot name="title">Payment History</x-slot>

    <h1 class="text-4xl font-bold mb-6">Payment History</h1>

    <div class="card overflow-hidden">
        <table class="w-full">
            <thead class="bg-gray-100">
                <tr>
                    <th class="px-6 py-3 text-left">Date</th>
                    <th class="px-6 py-3 text-left">Type</th>
                    <th class="px-6 py-3 text-left">Method</th>
                    <th class="px-6 py-3 text-right">Amount</th>
                    <th class="px-6 py-3 text-left">Status</th>
                </tr>
            </thead>
            <tbody>
                @forelse ($payments as $payment)
                    <tr class="border-t">
                        <td class="px-6 py-3">{{ $payment->created_at->format('Y-m-d H:i') }}</td>
                        <td class="px-6 py-3">
                            @if ($payment->payment_type === \App\Enums\PaymentType::Membership)
                                Membership
                            @else
                                Credits
                            @endif
                        </td>
                        <td class="px-6 py-3">
                            @if ($payment->payment_method === \App\Enums\PaymentMethod::Cash)
                                <span class="text-gray-600">Cash</span>
                            @else
                                <span class="text-blue-600">Online</span>
                            @endif
                        </td>
                        <td class="px-6 py-3 text-right">€{{ number_format($payment->amount_cents / 100, 2) }}</td>
                        <td class="px-6 py-3">
                            @if ($payment->status === \App\Enums\PaymentStatus::Completed)
                                <span class="badge-success">Completed</span>
                            @elseif ($payment->status === \App\Enums\PaymentStatus::Pending)
                                <span class="badge-warning">Pending</span>
                            @elseif ($payment->status === \App\Enums\PaymentStatus::Failed)
                                <span class="badge-danger">Failed</span>
                            @else
                                <span class="bg-gray-100 text-gray-800 px-3 py-1 rounded text-sm">{{ ucfirst($payment->status->value) }}</span>
                            @endif
                        </td>
                    </tr>
                @empty
                    <tr>
                        <td colspan="5" class="px-6 py-8 text-center text-gray-700">
                            No payments found.
                        </td>
                    </tr>
                @endforelse
            </tbody>
        </table>
    </div>
</x-app-layout>
