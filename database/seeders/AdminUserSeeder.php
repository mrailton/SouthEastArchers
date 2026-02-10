<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

class AdminUserSeeder extends Seeder
{
    /**
     * Run the database seeds.
     */
    public function run(): void
    {
        $admin = User::firstOrCreate(
            ['email' => 'admin@southeastarchers.ie'],
            [
                'name' => 'Admin User',
                'email' => 'admin@southeastarchers.ie',
                'password' => Hash::make('password'),
                'phone' => '',
                'qualification' => '',
                'is_active' => true,
                'email_verified_at' => now(),
            ],
        );

        $admin->assignRole('Admin');
    }
}
