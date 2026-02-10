<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Spatie\Permission\Models\Permission;

class PermissionSeeder extends Seeder
{
    /**
     * The permissions to be created.
     *
     * @var array<string, string>
     */
    protected array $permissions = [
        'admin.dashboard.view' => 'Access admin dashboard',
        'settings.read' => 'View application settings',
        'settings.write' => 'Update application settings',
        'events.read' => 'List events',
        'events.create' => 'Create events',
        'events.update' => 'Edit events',
        'news.read' => 'List news articles',
        'news.create' => 'Create news articles',
        'news.update' => 'Edit news articles',
        'shoots.read' => 'List shoots',
        'shoots.create' => 'Create shoots',
        'shoots.update' => 'Edit shoots',
        'members.read' => 'View members',
        'members.create' => 'Create members',
        'members.update' => 'Edit members',
        'members.manage_membership' => 'Activate or renew memberships',
        'members.activate_account' => 'Activate user accounts',
        'roles.manage' => 'Manage roles and permissions',
        'payments.manage' => 'Manage and confirm payments',
    ];

    /**
     * Run the database seeds.
     */
    public function run(): void
    {
        foreach ($this->permissions as $name => $description) {
            Permission::firstOrCreate(
                ['name' => $name],
                ['guard_name' => 'web'],
            );
        }
    }
}
