@extends('layouts.app')

@section('title', 'Membership')

@section('content')
<div class="max-w-4xl">
    <h1 class="text-4xl font-bold mb-6">Membership</h1>
    
    <div class="bg-white p-8 rounded shadow mb-8">
        <h2 class="text-2xl font-bold mb-4">Annual Membership - €{{ number_format($annualCost, 0) }}</h2>
        <ul class="list-disc list-inside space-y-2 mb-6">
            <li>{{ $shootsIncluded }} shoots per year</li>
            <li>Access to member portal</li>
            <li>Community events and training</li>
            <li>Purchase additional credits as needed</li>
        </ul>
        @guest
            <a href="{{ route('register') }}" class="btn-primary px-6 py-2">Join Now</a>
        @endguest
    </div>
    
    <div class="bg-white p-8 rounded shadow">
        <h2 class="text-2xl font-bold mb-4">Additional Credits</h2>
        <p class="text-gray-700 mb-4">Need more shoots? Purchase additional credits at €{{ number_format($additionalShootCost, 0) }} per night.</p>
        @auth
            <a href="{{ route('credits') }}" class="text-blue-600 hover:underline">View your credits</a>
        @endauth
    </div>
</div>
@endsection
