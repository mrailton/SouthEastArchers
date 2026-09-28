<x-layouts.app>
    <div class="max-w-md mx-auto">
        <div class="card">
            <div class="text-center mb-8">
                <div class="inline-block p-2 mb-6">
                    <img src="{{ asset('images/logo.png') }}"
                         alt="South East Archers"
                         class="h-32 w-auto object-contain">
                </div>
                <h2 class="text-3xl font-bold text-primary">Welcome Back</h2>
                <p class="text-gray-600 mt-2">Login to your account</p>
            </div>

            <form method="POST" action="{{ route('login.post') }}" class="space-y-6">
                @csrf
                <div>
                    <label class="form-label" for="email">Email Address</label>
                    <input class="form-input"
                           type="email" name="email" id="email" required
                           placeholder="your.email@example.com">

                    <x-form.error field="email" />
                </div>

                <div>
                    <label class="form-label" for="password">Password</label>
                    <input class="form-input"
                           type="password" name="password" id="password" required
                           placeholder="Enter your password">

                    <x-form.error field="password" />
                </div>

                <button type="submit" class="w-full btn-primary py-3">
                    Login
                </button>
            </form>

            <div class="mt-6 text-center space-y-3">
                <p class="text-gray-700">
                    <a href="#" class="link-primary">Forgot your password?</a>
                </p>
                <p class="text-gray-700">
                    Don't have an account?
                    <a href="#" class="link-primary">Sign up here</a>
                </p>
            </div>
        </div>
    </div>
</x-layouts.app>
