<footer class="bg-gray-900 text-white mt-12 border-t-8" style="border-color: var(--sea-primary);">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-12">
            <div class="flex flex-col items-center md:items-start">
                <img src="{{ asset('images/logo.png') }}"
                     alt="South East Archers Logo"
                     class="h-32 w-auto object-contain mb-6 rounded-lg shadow-lg">
                <h3 class="text-xl font-bold mb-2">South East Archers</h3>
                <p class="text-gray-400 text-center md:text-left">Precision, Community, and Tradition in the South East.</p>
            </div>
            <div>
                <h4 class="text-lg font-bold mb-6 text-primary" style="color: var(--sea-primary-light);">Quick Links</h4>
                <ul class="space-y-4">
                    <li><a href="{{ route('index') }}" class="text-gray-400 hover:text-white transition-colors">Home</a></li>
                    <li><a href="{{ route('about') }}" class="text-gray-400 hover:text-white transition-colors">About Us</a></li>
                </ul>
            </div>
            <div>
                <h4 class="text-lg font-bold mb-6" style="color: var(--sea-red-light);">Members</h4>
                <ul class="space-y-4">
                    <li><a href="{{ route('login') }}" class="text-gray-400 hover:text-white transition-colors">Login</a></li>
                    <li><a href="#" class="text-gray-400 hover:text-white transition-colors">Join the Club</a></li>
                </ul>
            </div>
            <div>
                <h4 class="text-lg font-bold mb-6" style="color: var(--sea-gold-light);">Contact Us</h4>
                <p class="text-gray-400 mb-2">Email: info@southeastarchers.ie</p>
                <p class="text-gray-400 mb-4">Avoca, Ireland</p>
                <div class="flex space-x-4">
                    <!-- Social placeholders -->
                    <span class="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center hover:bg-primary transition-colors cursor-pointer">f</span>
                    <span class="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center hover:bg-primary transition-colors cursor-pointer">i</span>
                </div>
            </div>
        </div>
        <hr class="border-gray-800 my-10">
        <p class="text-center text-gray-500 text-sm font-medium">&copy; {{ now()->format('Y') }} South East Archers Archery Club. All rights reserved.</p>
    </div>
</footer>
