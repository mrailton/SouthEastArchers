@props([
'type' => 'info',
'message',
])

@php
    $styles = match ($type) {
    'success' => 'bg-green-100 text-green-800',
    'error' => 'bg-red-100 text-red-800',
    'warning' => 'bg-yellow-100 text-yellow-800',
    default => 'bg-blue-100 text-blue-800',
    };
@endphp

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
    <div
        x-data="{ visible: true }"
        x-show="visible"
        x-init="setTimeout(() => visible = false, 3000)"
        x-transition.opacity.duration.200ms
        role="alert"
        {{ $attributes->merge(['class' => "p-4 rounded-lg {$styles}"]) }}
    >
        <p class="text-sm font-medium leading-6">
            {{ $message }}
        </p>
    </div>
</div>
