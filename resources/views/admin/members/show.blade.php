@extends('layouts.app')

@section('title', $member->name)

@section('content')
<div class="max-w-4xl mx-auto" x-data="{ showActivateModal: false }">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-4xl font-bold">{{ $member->name }}</h1>
        @can('members.update')
        <a href="{{ route('admin.members.edit', $member) }}" class="btn-primary px-4 py-2">
            Edit Member
        </a>
        @endcan
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="bg-white p-6 rounded shadow">
            <h3 class="text-2xl font-bold mb-4">Member Info</h3>
            <p class="text-gray-700 mb-2"><strong>Email:</strong> {{ $member->email }}</p>
            <p class="text-gray-700 mb-2"><strong>Phone:</strong> {{ $member->phone ?: 'N/A' }}</p>
            <p class="text-gray-700 mb-2">
                <strong>Qualification:</strong> 
                @switch($member->qualification)
                    @case('none') None @break
                    @case('beginner') Beginner Course Completed @break
                    @case('ai') Archery Ireland Member @break
                    @case('ifaf') Irish Field Archery Federation Member @break
                    @default {{ ucfirst($member->qualification) }}
                @endswitch
            </p>
            <p class="text-gray-700 mb-2">
                <strong>Roles:</strong>
                @forelse($member->roles as $role)
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 mr-2">
                    {{ $role->name }}
                </span>
                @empty
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">Member</span>
                @endforelse
            </p>
            <p class="text-gray-700 mb-2">
                <strong>Status:</strong>
                <span class="{{ $member->is_active ? 'text-green-600' : 'text-red-600' }}">
                    {{ $member->is_active ? 'Active' : 'Inactive' }}
                </span>
            </p>

            @unless($member->is_active)
            <div class="mt-4 pt-4 border-t">
                <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
                    <p class="text-sm text-yellow-700">
                        This account is inactive. Activate to send welcome email.
                    </p>
                </div>
                @can('members.activate_account')
                <form method="POST" action="{{ route('admin.members.activate', $member) }}" onsubmit="return confirm('Activate this account and send welcome email?');">
                    @csrf
                    <button type="submit" class="w-full bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 font-semibold">
                        ✓ Activate Account & Send Welcome Email
                    </button>
                </form>
                @endcan
            </div>
            @endunless
        </div>
        
        <div class="bg-white p-6 rounded shadow">
            <h3 class="text-2xl font-bold mb-4">Membership</h3>
            @if($member->membership)
                <p class="text-gray-700 mb-2">
                    <strong>Status:</strong> 
                    <span class="badge {{ $member->membership->status === \App\Enums\MembershipStatus::Active ? 'badge-success' : ($member->membership->status === \App\Enums\MembershipStatus::Pending ? 'badge-warning' : 'badge-danger') }}">
                        {{ ucfirst($member->membership->status->value) }}
                    </span>
                </p>
                <p class="text-gray-700 mb-2"><strong>Start Date:</strong> {{ $member->membership->start_date->format('d M Y') }}</p>
                <p class="text-gray-700 mb-2"><strong>Expires:</strong> {{ $member->membership->expiry_date->format('d M Y') }}</p>
                <p class="text-gray-700 mb-4">
                    <strong>Credits:</strong> {{ $member->membership->creditsRemaining() }}
                    <span class="text-sm text-gray-500">({{ $member->membership->initial_credits }} initial + {{ $member->membership->purchased_credits }} purchased)</span>
                </p>
                
                @if($member->membership->status === \App\Enums\MembershipStatus::Pending)
                    <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
                        <p class="text-sm text-yellow-700">
                            Membership is pending payment confirmation.
                        </p>
                    </div>
                    @can('members.manage_membership')
                    <form method="POST" action="{{ route('admin.members.membership.activate', $member) }}" onsubmit="return confirm('Activate this membership?');">
                        @csrf
                        <button type="submit" class="w-full bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 font-semibold">
                            ✓ Activate Membership
                        </button>
                    </form>
                    @endcan
                @elseif(!$member->membership->isActive())
                    @can('members.manage_membership')
                    <form method="POST" action="{{ route('admin.members.membership.renew', $member) }}" onsubmit="return confirm('Renew this membership?');">
                        @csrf
                        <button type="submit" class="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 font-semibold">
                            Renew Membership
                        </button>
                    </form>
                    @endcan
                @endif
            @else
                <p class="text-gray-600 mb-4">No active membership</p>
                <p class="text-sm text-gray-500">Create a membership when editing this member.</p>
            @endif
        </div>
    </div>
    
    {{-- Payment History --}}
    @if($member->payments->count() > 0)
    <div class="mt-6 bg-white p-6 rounded shadow">
        <h3 class="text-2xl font-bold mb-4">Payment History</h3>
        <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Method</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        @can('payments.confirm')
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        @endcan
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    @foreach($member->payments->sortByDesc('created_at') as $payment)
                    <tr>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ $payment->created_at->format('d M Y') }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ ucfirst($payment->payment_type->value) }}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            <span class="badge {{ $payment->payment_method->value === 'online' ? 'badge-primary' : 'badge-secondary' }}">
                                {{ ucfirst($payment->payment_method->value) }}
                            </span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">€{{ number_format($payment->amount_cents / 100, 2) }}</td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <span class="badge {{ $payment->status === \App\Enums\PaymentStatus::Completed ? 'badge-success' : ($payment->status === \App\Enums\PaymentStatus::Pending ? 'badge-warning' : 'badge-danger') }}">
                                {{ ucfirst($payment->status->value) }}
                            </span>
                        </td>
                        @can('payments.confirm')
                        <td class="px-6 py-4 whitespace-nowrap text-sm">
                            @if($payment->status === \App\Enums\PaymentStatus::Pending && $payment->payment_method === \App\Enums\PaymentMethod::Cash)
                                <form action="{{ route('admin.payments.confirm', $payment) }}" method="POST" class="inline" onsubmit="return confirm('Are you sure you want to confirm this payment?')">
                                    @csrf
                                    <input type="hidden" name="redirect" value="{{ route('admin.members.show', $member) }}">
                                    <button type="submit" class="btn btn-primary text-sm px-3 py-1">
                                        Confirm
                                    </button>
                                </form>
                            @else
                                <span class="text-gray-400">-</span>
                            @endif
                        </td>
                        @endcan
                    </tr>
                    @endforeach
                </tbody>
            </table>
        </div>
    </div>
    @endif
    
    {{-- Shoot History --}}
    <div class="mt-6 bg-white p-6 rounded shadow">
        <h3 class="text-2xl font-bold mb-4">Shoot History</h3>
        @if($member->shoots->count() > 0)
            <p class="text-gray-700 mb-4"><strong>Total Shoots:</strong> {{ $member->shoots->count() }}</p>
            <div class="space-y-2">
                @foreach($member->shoots->sortByDesc('date')->take(10) as $shoot)
                <div class="flex justify-between py-2 border-b">
                    <span>{{ $shoot->date->format('d M Y') }} - {{ $shoot->location->value }}</span>
                </div>
                @endforeach
            </div>
        @else
            <p class="text-gray-600">No shoots attended yet</p>
        @endif
    </div>
    
    <div class="mt-6">
        <a href="{{ route('admin.members.index') }}" class="text-blue-600 hover:underline">&larr; Back to members</a>
    </div>
</div>
@endsection
