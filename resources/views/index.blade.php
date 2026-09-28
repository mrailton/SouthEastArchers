<x-layouts.app>
    <div class="hero">
        <div class="text-center px-4">
            <h1 class="hero-title">Welcome to South East Archers</h1>
            <p class="hero-subtitle">Join our archery club and discover the art of precision shooting</p>

            <div class="flex flex-col sm:flex-row gap-4 justify-center mt-8">
                <a href="#}" class="btn-primary px-8 py-4 text-lg">
                    Join Now
                </a>
            </div>
        </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
        <div class="bg-white p-8 rounded-xl shadow-md hover:shadow-xl transition-all duration-300 border-t-8" style="border-color: var(--sea-primary);">
            <div class="flex items-center justify-between mb-6">
                <span class="text-5xl">🏹</span>
                <img src="{{ asset('images/logo.png') }}" class="h-12 w-auto opacity-20 group-hover:opacity-100 transition-opacity">
            </div>
            <h3 class="text-2xl font-bold mb-4 text-primary">Expert Training</h3>
            <p class="text-gray-700">Learn from experienced instructors in a safe, supportive environment.</p>
        </div>

        <div class="bg-white p-8 rounded-xl shadow-md hover:shadow-xl transition-all duration-300 border-t-8" style="border-color: var(--sea-red);">
            <div class="flex items-center justify-between mb-6">
                <span class="text-5xl">🌟</span>
                <img src="{{ asset('images/logo.png') }}" class="h-12 w-auto opacity-20 group-hover:opacity-100 transition-opacity">
            </div>
            <h3 class="text-2xl font-bold mb-4 text-red">Community</h3>
            <p class="text-gray-700">Meet fellow archers and build lasting friendships with like-minded people.</p>
        </div>

        <div class="bg-white p-8 rounded-xl shadow-md hover:shadow-xl transition-all duration-300 border-t-8" style="border-color: var(--sea-burgundy);">
            <div class="flex items-center justify-between mb-6">
                <span class="text-5xl">🎯</span>
                <img src="{{ asset('images/logo.png') }}" class="h-12 w-auto opacity-20 group-hover:opacity-100 transition-opacity">
            </div>
            <h3 class="text-2xl font-bold mb-4 text-burgundy">All Levels</h3>
            <p class="text-gray-700">Whether you're a beginner or experienced archer, we have something for you.</p>
        </div>
    </div>
</x-layouts.app>
