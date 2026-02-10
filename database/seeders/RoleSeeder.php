<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Spatie\Permission\Models\Role;

class RoleSeeder extends Seeder
{
    /**
     * The roles and their permissions.
     *
     * @var array<string, array<string, string|list<string>>>
     */
    protected array $roles = [
        'Admin' => [
            'description' => 'Full access to all admin features',
            'permissions' => [
                'admin.dashboard.view',
                'settings.read',
                'settings.write',
                'events.read',
                'events.create',
                'events.update',
                'news.read',
                'news.create',
                'news.update',
                'shoots.read',
                'shoots.create',
                'shoots.update',
                'members.read',
                'members.create',
                'members.update',
                'members.manage_membership',
                'members.activate_account',
                'roles.manage',
                'payments.manage',
                'payments.confirm',
            ],
        ],
        'Membership Manager' => [
            'description' => 'Manage members, memberships, and shoots',
            'permissions' => [
                'admin.dashboard.view',
                'members.read',
                'members.create',
                'members.update',
                'members.manage_membership',
                'members.activate_account',
                'shoots.read',
                'shoots.create',
                'shoots.update',
                'payments.manage',
                'payments.confirm',
            ],
        ],
        'Content Manager' => [
            'description' => 'Manage events and news content',
            'permissions' => [
                'admin.dashboard.view',
                'events.read',
                'events.create',
                'events.update',
                'news.read',
                'news.create',
                'news.update',
            ],
        ],
        'Settings Manager' => [
            'description' => 'Manage application settings',
            'permissions' => [
                'admin.dashboard.view',
                'settings.read',
                'settings.write',
            ],
        ],
    ];

    /**
     * Run the database seeds.
     */
    public function run(): void
    {
        foreach ($this->roles as $name => $config) {
            $role = Role::firstOrCreate(
                ['name' => $name],
                ['guard_name' => 'web'],
            );

            $role->syncPermissions($config['permissions']);
        }
    }
}
