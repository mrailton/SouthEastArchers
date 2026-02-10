@extends('layouts.app')

@section('title', 'Settings')

@section('content')
<div class="max-w-2xl mx-auto">
    <h1 class="text-4xl font-bold mb-6">Application Settings</h1>
    
    <div class="bg-white p-8 rounded shadow">
        <form method="POST" action="{{ route('admin.settings.update') }}" class="space-y-6">
            @csrf
            @method('PUT')
            
            <div class="border-b pb-6 mb-6">
                <h2 class="text-xl font-bold mb-4">Membership Year</h2>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label for="membership_year_start_month" class="block text-gray-700 font-bold mb-2">Start Month</label>
                        <select class="w-full border border-gray-300 rounded px-3 py-2" id="membership_year_start_month" name="membership_year_start_month">
                            @for($i = 1; $i <= 12; $i++)
                            <option value="{{ $i }}" {{ $settings->membership_year_start_month == $i ? 'selected' : '' }}>
                                {{ DateTime::createFromFormat('!m', $i)->format('F') }}
                            </option>
                            @endfor
                        </select>
                    </div>
                    <div>
                        <label for="membership_year_start_day" class="block text-gray-700 font-bold mb-2">Start Day</label>
                        <input class="w-full border border-gray-300 rounded px-3 py-2" type="number" id="membership_year_start_day" name="membership_year_start_day" value="{{ $settings->membership_year_start_day }}" min="1" max="31">
                    </div>
                </div>
            </div>
            
            <div class="border-b pb-6 mb-6">
                <h2 class="text-xl font-bold mb-4">Pricing</h2>
                <div class="space-y-4">
                    <div>
                        <label for="annual_membership_cost" class="block text-gray-700 font-bold mb-2">Annual Membership Cost (€)</label>
                        <input class="w-full border border-gray-300 rounded px-3 py-2" type="number" id="annual_membership_cost" name="annual_membership_cost" value="{{ $settings->annual_membership_cost / 100 }}" step="0.01" min="0">
                    </div>
                    <div>
                        <label for="membership_shoots_included" class="block text-gray-700 font-bold mb-2">Shoots Included in Membership</label>
                        <input class="w-full border border-gray-300 rounded px-3 py-2" type="number" id="membership_shoots_included" name="membership_shoots_included" value="{{ $settings->membership_shoots_included }}" min="0">
                    </div>
                    <div>
                        <label for="additional_shoot_cost" class="block text-gray-700 font-bold mb-2">Additional Shoot Cost (€)</label>
                        <input class="w-full border border-gray-300 rounded px-3 py-2" type="number" id="additional_shoot_cost" name="additional_shoot_cost" value="{{ $settings->additional_shoot_cost / 100 }}" step="0.01" min="0">
                    </div>
                </div>
            </div>
            
            <button type="submit" class="btn-primary py-2 px-6">Save Settings</button>
        </form>
    </div>
</div>
@endsection
