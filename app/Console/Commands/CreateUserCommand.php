<?php

namespace App\Console\Commands;

use App\Models\User;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Hash;

use function Laravel\Prompts\multiselect;
use function Laravel\Prompts\password;
use function Laravel\Prompts\select;
use function Laravel\Prompts\text;

use Spatie\Permission\Models\Role;

class CreateUserCommand extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'user:create';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Create a new user with roles';

    /**
     * Execute the console command.
     */
    public function handle(): int
    {
        $name = text(
            label: 'Name',
            required: true,
            validate: fn (string $value) => strlen($value) > 255 ? 'Name must be 255 characters or less.' : null,
        );

        $email = text(
            label: 'Email',
            required: true,
            validate: function (string $value) {
                if (! filter_var($value, FILTER_VALIDATE_EMAIL)) {
                    return 'Please enter a valid email address.';
                }
                if (strlen($value) > 255) {
                    return 'Email must be 255 characters or less.';
                }
                if (User::where('email', strtolower($value))->exists()) {
                    return 'This email is already registered.';
                }

                return null;
            },
        );

        $phone = text(
            label: 'Phone Number (optional)',
            required: false,
            validate: fn (string $value) => strlen($value) > 50 ? 'Phone number must be 50 characters or less.' : null,
        );

        $password = password(
            label: 'Password',
            required: true,
            validate: fn (string $value) => strlen($value) < 8 ? 'Password must be at least 8 characters.' : null,
        );

        password(
            label: 'Confirm Password',
            required: true,
            validate: fn (string $value) => $value !== $password ? 'Passwords do not match.' : null,
        );

        $qualification = select(
            label: 'Qualification',
            options: [
                'none' => 'None',
                'beginner' => 'Beginner',
                'ai' => 'Archery Ireland',
                'ifaf' => 'IFAF',
            ],
            required: true,
        );

        $roles = Role::pluck('name', 'id')->toArray();

        $selectedRoles = [];
        if (count($roles) > 0) {
            $selectedRoles = multiselect(
                label: 'Select roles to assign',
                options: $roles,
                required: false,
            );
        }

        $user = User::create([
            'name' => $name,
            'email' => strtolower($email),
            'phone' => $phone ?: null,
            'password' => Hash::make($password),
            'qualification' => $qualification,
            'is_active' => true,
        ]);

        if (count($selectedRoles) > 0) {
            $roleNames = Role::whereIn('id', $selectedRoles)->pluck('name')->toArray();
            $user->assignRole($roleNames);
        }

        $this->info("User '{$user->name}' created successfully with email '{$user->email}'.");

        if (count($selectedRoles) > 0) {
            $this->info('Assigned roles: ' . implode(', ', $roleNames));
        }

        return Command::SUCCESS;
    }
}
