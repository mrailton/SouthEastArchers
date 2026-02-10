<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="csrf-token" content="{{ csrf_token() }}">

        <title>@yield('title', config('app.name', 'South East Archers'))</title>

        <!-- Fonts -->
        <link rel="preconnect" href="https://fonts.bunny.net">
        <link href="https://fonts.bunny.net/css?family=figtree:400,500,600,700&display=swap" rel="stylesheet" />

        <!-- Scripts -->
        @vite(['resources/css/app.css', 'resources/js/app.js'])
    </head>
    <body class="font-sans text-gray-900 antialiased">
        <div class="min-h-screen flex flex-col sm:justify-center items-center pt-6 sm:pt-0 bg-gray-100">
            <div class="mb-4">
                <a href="{{ route('home') }}" class="flex flex-col items-center">
                    <img src="{{ asset('images/logo.jpeg') }}"
                         alt="South East Archers Logo"
                         class="h-24 w-auto object-contain mb-2">
                    <span class="text-xl font-bold" style="color: var(--sea-primary);">South East Archers</span>
                </a>
            </div>

            <!-- Flash messages -->
            @if (session('success') || session('error') || session('warning') || session('info') || session('status'))
                <div class="w-full sm:max-w-md px-6 mb-4">
                    @if (session('success'))
                        <div class="p-4 rounded-lg bg-green-100 text-green-800">
                            {{ session('success') }}
                        </div>
                    @endif
                    @if (session('error'))
                        <div class="p-4 rounded-lg bg-red-100 text-red-800">
                            {{ session('error') }}
                        </div>
                    @endif
                    @if (session('warning'))
                        <div class="p-4 rounded-lg bg-yellow-100 text-yellow-800">
                            {{ session('warning') }}
                        </div>
                    @endif
                    @if (session('info') || session('status'))
                        <div class="p-4 rounded-lg bg-blue-100 text-blue-800">
                            {{ session('info') ?? session('status') }}
                        </div>
                    @endif
                </div>
            @endif

            <div class="w-full sm:max-w-md px-6 py-4 bg-white shadow-md overflow-hidden sm:rounded-lg">
                {{ $slot }}
            </div>
        </div>
    </body>
</html>
