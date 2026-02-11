<x-guest-layout>
    <div class="text-center mb-8">
        <h2 class="text-3xl font-bold text-primary">Forgot Password</h2>
        <p class="text-gray-600 mt-2">We'll send you a reset link</p>
    </div>

    <p class="text-gray-700 mb-6">Enter your email address and we'll send you a link to reset your password.</p>

    <!-- Session Status -->
    <x-auth-session-status class="mb-4" :status="session('status')" />

    <form method="POST" action="{{ route('password.email') }}" class="space-y-6">
        @csrf

        <!-- Email Address -->
        <div>
            <label class="form-label" for="email">Email Address</label>
            <input class="form-input"
                   type="email" id="email" name="email"
                   value="{{ old('email') }}"
                   required autofocus
                   placeholder="your.email@example.com">
            <x-input-error :messages="$errors->get('email')" class="mt-2" />
        </div>

        <button type="submit" class="w-full btn-primary py-3">
            Send Reset Link
        </button>
    </form>

    <div class="text-center mt-6">
        <a href="{{ route('login') }}" class="link-primary">Back to login</a>
    </div>
</x-guest-layout>
