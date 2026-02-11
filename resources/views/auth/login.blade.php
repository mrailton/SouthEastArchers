<x-guest-layout>
    <div class="text-center mb-8">
        <h2 class="text-3xl font-bold text-primary">Welcome Back</h2>
        <p class="text-gray-600 mt-2">Login to your account</p>
    </div>

    <!-- Session Status -->
    <x-auth-session-status class="mb-4" :status="session('status')" />

    <form method="POST" action="{{ route('login') }}" class="space-y-6">
        @csrf

        <!-- Email Address -->
        <div>
            <label class="form-label" for="email">Email Address</label>
            <input class="form-input"
                   type="email" name="email" id="email"
                   value="{{ old('email') }}"
                   required autofocus autocomplete="username"
                   placeholder="your.email@example.com">
            <x-input-error :messages="$errors->get('email')" class="mt-2" />
        </div>

        <!-- Password -->
        <div>
            <label class="form-label" for="password">Password</label>
            <input class="form-input"
                   type="password" name="password" id="password"
                   required autocomplete="current-password"
                   placeholder="Enter your password">
            <x-input-error :messages="$errors->get('password')" class="mt-2" />
        </div>

        <button type="submit" class="w-full btn-primary py-3">
            Login
        </button>
    </form>

    <div class="mt-6 text-center space-y-3">
        <p class="text-gray-700">
            <a href="{{ route('password.request') }}" class="link-primary">Forgot your password?</a>
        </p>
        <p class="text-gray-700">
            Don't have an account?
            <a href="{{ route('register') }}" class="link-primary">Sign up here</a>
        </p>
    </div>
</x-guest-layout>
