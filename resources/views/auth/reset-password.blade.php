<x-guest-layout>
    <div class="text-center mb-8">
        <h2 class="text-3xl font-bold text-primary">Reset Password</h2>
        <p class="text-gray-600 mt-2">Choose a new password</p>
    </div>

    <form method="POST" action="{{ route('password.store') }}" class="space-y-6">
        @csrf

        <!-- Password Reset Token -->
        <input type="hidden" name="token" value="{{ $request->route('token') }}">

        <!-- Email Address -->
        <div>
            <label class="form-label" for="email">Email Address</label>
            <input class="form-input"
                   type="email" id="email" name="email"
                   value="{{ old('email', $request->email) }}"
                   required autofocus autocomplete="username">
            <x-input-error :messages="$errors->get('email')" class="mt-2" />
        </div>

        <!-- Password -->
        <div>
            <label class="form-label" for="password">New Password</label>
            <input class="form-input"
                   type="password" id="password" name="password"
                   required autocomplete="new-password"
                   placeholder="Enter new password">
            <x-input-error :messages="$errors->get('password')" class="mt-2" />
        </div>

        <!-- Confirm Password -->
        <div>
            <label class="form-label" for="password_confirmation">Confirm Password</label>
            <input class="form-input"
                   type="password" id="password_confirmation" name="password_confirmation"
                   required autocomplete="new-password"
                   placeholder="Confirm new password">
            <x-input-error :messages="$errors->get('password_confirmation')" class="mt-2" />
        </div>

        <button type="submit" class="w-full btn-primary py-3">
            Reset Password
        </button>
    </form>
</x-guest-layout>
