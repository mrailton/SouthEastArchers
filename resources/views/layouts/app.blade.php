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

    @stack('styles')
</head>
<body class="font-sans antialiased bg-gray-50">
    <!-- Navigation -->
    <nav class="bg-white shadow-md border-b-4" style="border-color: var(--sea-primary);" x-data="{ open: false }">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-32">
                <div class="flex items-center">
                    <a href="{{ route('home') }}" class="flex items-center space-x-4 group">
                        <div class="relative p-1 bg-white rounded-full shadow-inner border border-gray-100">
                            <img src="{{ asset('images/logo.jpeg') }}"
                                 alt="South East Archers Logo"
                                 class="h-28 w-auto object-contain transition-transform duration-300 group-hover:scale-110"
                                 style="filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));">
                        </div>
                        <div class="hidden md:block">
                            <div class="text-2xl font-bold transition-colors duration-300" style="color: var(--sea-primary);">
                                South East Archers
                            </div>
                            <div class="text-sm font-semibold" style="color: var(--sea-red);">Archery Club</div>
                        </div>
                    </a>
                </div>

                <!-- Mobile menu button -->
                <button @click="open = !open" class="md:hidden">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M4 6h16M4 12h16M4 18h16"></path>
                    </svg>
                </button>

                <!-- Desktop menu -->
                <div class="hidden md:flex items-center space-x-6">
                    <a href="{{ route('home') }}" class="nav-link text-gray-700 font-medium">Home</a>
                    <a href="{{ route('about') }}" class="nav-link text-gray-700 font-medium">About</a>
                    <a href="{{ route('news') }}" class="nav-link text-gray-700 font-medium">News</a>
                    <a href="{{ route('events') }}" class="nav-link text-gray-700 font-medium">Events</a>

                    @auth
                        <a href="{{ route('dashboard') }}" class="nav-link text-gray-700 font-medium">Dashboard</a>
                        @can('admin.dashboard.view')
                            <a href="{{ route('admin.dashboard') }}" class="badge-red px-4 py-2 rounded-lg">Admin</a>
                        @endcan
                        <form method="POST" action="{{ route('logout') }}" class="inline">
                            @csrf
                            <button type="submit" class="text-gray-600 hover:text-red-600 font-medium">Logout</button>
                        </form>
                    @else
                        <a href="{{ route('membership') }}" class="nav-link text-gray-700 font-medium">Membership</a>
                        <a href="{{ route('login') }}" class="nav-link text-gray-700 font-medium">Login</a>
                        <a href="{{ route('register') }}" class="btn-secondary px-6 py-2">Sign Up</a>
                    @endauth
                </div>
            </div>

            <!-- Mobile menu -->
            <div x-show="open" x-cloak class="md:hidden pb-4 space-y-2">
                <a href="{{ route('home') }}" class="block py-2 text-gray-700 hover:text-primary">Home</a>
                <a href="{{ route('about') }}" class="block py-2 text-gray-700 hover:text-primary">About</a>
                <a href="{{ route('news') }}" class="block py-2 text-gray-700 hover:text-primary">News</a>
                <a href="{{ route('events') }}" class="block py-2 text-gray-700 hover:text-primary">Events</a>

                @auth
                    <a href="{{ route('dashboard') }}" class="block py-2 text-gray-700 hover:text-primary">Dashboard</a>
                    @can('admin.dashboard.view')
                        <a href="{{ route('admin.dashboard') }}" class="block py-2 font-semibold text-red">Admin</a>
                    @endcan
                    <form method="POST" action="{{ route('logout') }}">
                        @csrf
                        <button type="submit" class="block py-2 text-gray-600 hover:text-red">Logout</button>
                    </form>
                @else
                    <a href="{{ route('membership') }}" class="block py-2 text-gray-700 hover:text-primary">Membership</a>
                    <a href="{{ route('login') }}" class="block py-2 text-gray-700 hover:text-primary">Login</a>
                    <a href="{{ route('register') }}" class="block py-2 text-red font-semibold">Sign Up</a>
                @endauth
            </div>
        </div>
    </nav>

    <!-- Flash messages -->
    @if (session('success') || session('error') || session('warning') || session('info') || session('status'))
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
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

    <!-- Main content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        @hasSection('content')
            @yield('content')
        @else
            {{ $slot ?? '' }}
        @endif
    </main>

    <!-- Footer -->
    <footer class="bg-gray-900 text-white mt-12 border-t-8" style="border-color: var(--sea-primary);">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-12">
                <div class="flex flex-col items-center md:items-start">
                    <img src="{{ asset('images/logo.jpeg') }}"
                         alt="South East Archers Logo"
                         class="h-32 w-auto object-contain mb-6 rounded-lg shadow-lg">
                    <h3 class="text-xl font-bold mb-2">South East Archers</h3>
                    <p class="text-gray-400 text-center md:text-left">Precision, Community, and Tradition in the South East.</p>
                </div>
                <div>
                    <h4 class="text-lg font-bold mb-6 text-primary" style="color: var(--sea-primary-light);">Quick Links</h4>
                    <ul class="space-y-4">
                        <li><a href="{{ route('home') }}" class="text-gray-400 hover:text-white transition-colors">Home</a></li>
                        <li><a href="{{ route('about') }}" class="text-gray-400 hover:text-white transition-colors">About Us</a></li>
                        <li><a href="{{ route('news') }}" class="text-gray-400 hover:text-white transition-colors">Latest News</a></li>
                        <li><a href="{{ route('events') }}" class="text-gray-400 hover:text-white transition-colors">Upcoming Events</a></li>
                    </ul>
                </div>
                <div>
                    <h4 class="text-lg font-bold mb-6" style="color: var(--sea-red-light);">Members</h4>
                    <ul class="space-y-4">
                        @auth
                            <li><a href="{{ route('dashboard') }}" class="text-gray-400 hover:text-white transition-colors">Dashboard</a></li>
                            <li><a href="{{ route('profile') }}" class="text-gray-400 hover:text-white transition-colors">My Profile</a></li>
                            <li>
                                <form method="POST" action="{{ route('logout') }}" class="inline">
                                    @csrf
                                    <button type="submit" class="text-gray-400 hover:text-white transition-colors">Logout</button>
                                </form>
                            </li>
                        @else
                            <li><a href="{{ route('login') }}" class="text-gray-400 hover:text-white transition-colors">Login</a></li>
                            <li><a href="{{ route('register') }}" class="text-gray-400 hover:text-white transition-colors">Join the Club</a></li>
                        @endauth
                    </ul>
                </div>
                <div>
                    <h4 class="text-lg font-bold mb-6" style="color: var(--sea-gold-light);">Contact Us</h4>
                    <p class="text-gray-400 mb-2">Email: info@southeastarchers.ie</p>
                    <p class="text-gray-400 mb-4">Avoca, Ireland</p>
                    <div class="flex space-x-4">
                        <span class="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center hover:bg-primary transition-colors cursor-pointer">f</span>
                        <span class="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center hover:bg-primary transition-colors cursor-pointer">i</span>
                    </div>
                </div>
            </div>
            <hr class="border-gray-800 my-10">
            <p class="text-center text-gray-500 text-sm font-medium">&copy; {{ date('Y') }} South East Archers Archery Club. All rights reserved.</p>
        </div>
    </footer>

    @stack('scripts')
</body>
</html>
