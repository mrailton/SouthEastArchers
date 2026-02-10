@extends('layouts.app')

@section('title', 'Credits')

@section('content')
<h1 class="text-4xl font-bold mb-6">Your Credits</h1>

<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
    <div class="bg-white p-6 rounded shadow">
        <h2 class="text-2xl font-bold mb-4">Available Credits</h2>
        @if($user->membership)
            <div class="text-center py-8">
                <p class="text-6xl font-bold text-blue-600 mb-2">{{ $user->membership->creditsRemaining() }}</p>
                <p class="text-gray-600">Shooting credits remaining</p>
            </div>
            
            @if($credits->count() > 0)
            <div class="mt-6 border-t pt-4">
                <h3 class="font-semibold mb-3">Purchase History</h3>
                <div class="space-y-2">
                @foreach($credits as $credit)
                    <div class="bg-gray-50 p-3 rounded text-sm">
                        <p class="font-bold">{{ $credit->amount }} credit{{ $credit->amount != 1 ? 's' : '' }}</p>
                        <p class="text-gray-600">Purchased: {{ $credit->created_at->format('Y-m-d') }}</p>
                    </div>
                @endforeach
                </div>
            </div>
            @endif
        @else
            <p class="text-gray-700">You don't have an active membership.</p>
            <a href="{{ route('payment.membership') }}" class="mt-4 inline-block btn-primary px-4 py-2">
                Purchase Membership
            </a>
        @endif
    </div>
    
    <div class="bg-blue-50 p-6 rounded shadow">
        <h2 class="text-2xl font-bold mb-4">Purchase Credits</h2>
        <p class="text-gray-700 mb-4">€{{ number_format($additionalShootCost, 0) }} per shooting credit</p>
        <a href="{{ route('payment.credits') }}" class="block w-full text-center btn-primary py-3">
            Purchase Additional Credits
        </a>
    </div>
</div>
@endsection
