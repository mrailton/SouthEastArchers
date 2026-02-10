@extends('layouts.app')

@section('title', 'Pending Cash Payments')

@section('content')
<div class="max-w-4xl mx-auto">
    <h1 class="text-3xl font-bold mb-6">Pending Cash Payments</h1>
    
    @if($payments->count() > 0)
    <div class="bg-white shadow overflow-hidden sm:rounded-md">
        <ul class="divide-y divide-gray-200">
            @foreach($payments as $payment)
            <li class="px-6 py-4">
                <div class="flex items-center justify-between">
                    <div>
                        <h3 class="text-lg font-medium text-gray-900">{{ $payment->user->name }}</h3>
                        <p class="text-sm text-gray-600">{{ $payment->user->email }}</p>
                        <p class="mt-1 text-sm text-gray-500">
                            {{ ucfirst($payment->payment_type->value) }} - 
                            €{{ number_format($payment->amount_cents / 100, 2) }}
                        </p>
                        <p class="text-xs text-gray-400">{{ $payment->created_at->diffForHumans() }}</p>
                    </div>
                    <form method="POST" action="{{ route('admin.payments.confirm', $payment) }}" onsubmit="return confirm('Confirm this cash payment?');">
                        @csrf
                        <button type="submit" class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 font-semibold">
                            ✓ Confirm Payment
                        </button>
                    </form>
                </div>
            </li>
            @endforeach
        </ul>
    </div>
    <div class="mt-6">{{ $payments->links() }}</div>
    @else
    <div class="bg-white p-6 rounded shadow">
        <p class="text-gray-600">No pending cash payments.</p>
    </div>
    @endif
</div>
@endsection
