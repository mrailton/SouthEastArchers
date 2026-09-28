<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>South East Archers</title>

    @vite(['resources/css/app.css', 'resources/js/app.js'])

    <!-- Prevent flash of wrong theme -->
    <script>
        (function(){
            var t = localStorage.getItem('theme');
            if (t === 'dark' || (!t && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                document.documentElement.classList.add('dark');
            }
        })();
    </script>

    <style>
        [x-cloak] { display: none !important; }
    </style>
</head>
<body class="bg-gray-50">
<!-- Navigation -->
<nav class="bg-white shadow-md border-b-4" style="border-color: var(--sea-primary);" x-data="mobileNav">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-32">
            <div class="flex items-center">
                <a href="{{ route('index') }}" class="flex items-center space-x-4 group">
                    <div class="relative p-1">
                        <img src="{{ asset('images/logo.png') }}"
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
            <button @click="toggle" class="md:hidden">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M4 6h16M4 12h16M4 18h16"></path>
                </svg>
            </button>

            <!-- Desktop menu -->
            <div class="hidden md:flex items-center space-x-6">
                <a href="{{ route('index') }}" class="nav-link text-gray-700 font-medium">Home</a>
                <a href="{{ route('about') }}" class="nav-link text-gray-700 font-medium">About</a>
                <a href="{{ route('membership') }}" class="nav-link text-gray-700 font-medium">Membership</a>
                @guest
                    <a href="{{ route('login') }}" class="nav-link text-gray-700 font-medium">Login</a>
                @endguest

                @auth
                    <span x-data @click="$dispatch('open-modal', 'logout-modal')"class="cursor-pointer nav-link text-gray-700 font-medium">Logout</span>
                @endauth


                <!-- Dark mode toggle -->
                <div x-data="darkMode">
                    <button @click="toggle" class="dark-toggle" title="Toggle dark mode">
                        <!-- Sun icon (shown in dark mode) -->
                        <svg x-show="dark" x-cloak class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z"/>
                        </svg>
                        <!-- Moon icon (shown in light mode) -->
                        <svg x-show="!dark" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>

        <!-- Mobile menu -->
        <div x-show="open" class="md:hidden pb-4 space-y-2">
            <a href="{{ route('index') }}" class="block py-2 text-gray-700 hover:text-primary">Home</a>
            <a href="{{ route('about') }}" class="block py-2 text-gray-700 hover:text-primary">About</a>

            <a href="{{ route('membership') }}" class="block py-2 text-gray-700 hover:text-primary">Membership</a>
            <a href="{{ route('login') }}" class="block py-2 text-gray-700 hover:text-primary">Login</a>
            <a href="#" class="block py-2 text-red font-semibold">Sign Up</a>

            <!-- Mobile dark mode toggle -->
            <div x-data="darkMode" class="pt-2 border-t border-gray-200">
                <button @click="toggle" class="flex items-center gap-2 py-2 text-gray-700 dark-toggle">
                    <svg x-show="dark" x-cloak class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z"/>
                    </svg>
                    <svg x-show="!dark" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z"/>
                    </svg>
                    <span x-text="dark ? 'Light Mode' : 'Dark Mode'" class="text-sm font-medium"></span>
                </button>
            </div>
        </div>
    </div>
</nav>

@foreach (['success', 'error', 'warning', 'info'] as $type)
    @if (session()->has($type))
        <x-flash-messages
            :type="$type"
            :message="session($type)"
        />
    @endif
@endforeach

<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    {{ $slot }}
</main>

<x-footer />

<x-auth.logout-modal />
</body>
</html>
