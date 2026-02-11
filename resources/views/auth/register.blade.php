<x-guest-layout>
    <div class="text-center mb-8">
        <h2 class="text-3xl font-bold text-primary">Join Our Club</h2>
        <p class="text-gray-600 mt-2">Create your account to get started</p>
    </div>

    <form method="POST" action="{{ route('register') }}" class="space-y-4">
        @csrf

        <!-- Name -->
        <div>
            <label for="name" class="block text-gray-700 font-bold mb-2">Full Name *</label>
            <input class="w-full border border-gray-300 rounded px-3 py-2"
                   type="text" id="name" name="name" value="{{ old('name') }}" required autofocus autocomplete="name">
            <x-input-error :messages="$errors->get('name')" class="mt-2" />
        </div>

        <!-- Email Address -->
        <div>
            <label for="email" class="block text-gray-700 font-bold mb-2">Email Address *</label>
            <input class="w-full border border-gray-300 rounded px-3 py-2"
                   type="email" id="email" name="email" value="{{ old('email') }}" required autocomplete="username">
            <x-input-error :messages="$errors->get('email')" class="mt-2" />
        </div>

        <!-- Phone -->
        <div>
            <label for="phone" class="block text-gray-700 font-bold mb-2">Phone Number (optional)</label>
            <input class="w-full border border-gray-300 rounded px-3 py-2"
                   type="tel" id="phone" name="phone" value="{{ old('phone') }}">
            <x-input-error :messages="$errors->get('phone')" class="mt-2" />
        </div>

        <!-- Password -->
        <div>
            <label for="password" class="block text-gray-700 font-bold mb-2">Password *</label>
            <input class="w-full border border-gray-300 rounded px-3 py-2"
                   type="password" id="password" name="password" required autocomplete="new-password">
            <x-input-error :messages="$errors->get('password')" class="mt-2" />
        </div>

        <!-- Confirm Password -->
        <div>
            <label for="password_confirmation" class="block text-gray-700 font-bold mb-2">Confirm Password *</label>
            <input class="w-full border border-gray-300 rounded px-3 py-2"
                   type="password" id="password_confirmation" name="password_confirmation" required autocomplete="new-password">
            <x-input-error :messages="$errors->get('password_confirmation')" class="mt-2" />
        </div>

        <!-- Qualification Selection -->
        <div class="border-t pt-4 mt-4">
            <label class="block text-gray-700 font-bold mb-3">Qualification *</label>
            <div class="space-y-3">
                <div class="flex items-start">
                    <input type="radio"
                           id="qualification_none"
                           name="qualification"
                           value="none"
                           class="mt-1 mr-3"
                           {{ old('qualification', 'none') == 'none' ? 'checked' : '' }}>
                    <div>
                        <label for="qualification_none" class="font-semibold text-gray-900 cursor-pointer">
                            None
                        </label>
                        <p class="text-sm text-gray-600">
                            Select this if you have never taken a beginners course and are not a member of Archery Ireland or the Irish Field Archery Federation.
                        </p>
                    </div>
                </div>

                <div class="flex items-start">
                    <input type="radio"
                           id="qualification_beginner"
                           name="qualification"
                           value="beginner"
                           class="mt-1 mr-3"
                           {{ old('qualification') == 'beginner' ? 'checked' : '' }}>
                    <div>
                        <label for="qualification_beginner" class="font-semibold text-gray-900 cursor-pointer">
                            Beginner Course Completed
                        </label>
                        <p class="text-sm text-gray-600">
                            Select this if you have completed a recognised beginners course but are not a member of Archery Ireland or the Irish Field Archery Federation.
                        </p>
                    </div>
                </div>

                <div class="flex items-start">
                    <input type="radio"
                           id="qualification_ai"
                           name="qualification"
                           value="ai"
                           class="mt-1 mr-3"
                           {{ old('qualification') == 'ai' ? 'checked' : '' }}>
                    <div>
                        <label for="qualification_ai" class="font-semibold text-gray-900 cursor-pointer">
                            Archery Ireland Member
                        </label>
                        <p class="text-sm text-gray-600">
                            Select this if you have completed a recognised beginners course and are a member of Archery Ireland.
                        </p>
                    </div>
                </div>

                <div class="flex items-start">
                    <input type="radio"
                           id="qualification_ifaf"
                           name="qualification"
                           value="ifaf"
                           class="mt-1 mr-3"
                           {{ old('qualification') == 'ifaf' ? 'checked' : '' }}>
                    <div>
                        <label for="qualification_ifaf" class="font-semibold text-gray-900 cursor-pointer">
                            Irish Field Archery Federation Member
                        </label>
                        <p class="text-sm text-gray-600">
                            Select this if you have completed a recognised beginners course and are a member of the Irish Field Archery Federation.
                        </p>
                    </div>
                </div>
            </div>
            <x-input-error :messages="$errors->get('qualification')" class="mt-2" />
        </div>

        <button type="submit" class="w-full btn-secondary py-3">
            Create Account
        </button>
    </form>

    <div class="text-center mt-6">
        <p class="text-gray-700">
            Already have an account?
            <a href="{{ route('login') }}" class="link-primary">Login here</a>
        </p>
    </div>
</x-guest-layout>
