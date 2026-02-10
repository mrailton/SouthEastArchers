<?php

use App\Models\Event;
use App\Models\News;
use App\Models\Shoot;
use App\Models\User;
use Spatie\Permission\Models\Permission;
use Spatie\Permission\Models\Role;

beforeEach(function () {
    // Create required permissions
    Permission::findOrCreate('admin.dashboard.view');
    Permission::findOrCreate('shoots.read');
    Permission::findOrCreate('shoots.create');
    Permission::findOrCreate('shoots.update');
    Permission::findOrCreate('events.read');
    Permission::findOrCreate('events.create');
    Permission::findOrCreate('events.update');
    Permission::findOrCreate('news.read');
    Permission::findOrCreate('news.create');
    Permission::findOrCreate('news.update');

    $adminRole = Role::findOrCreate('Admin');
    $adminRole->givePermissionTo(Permission::all());
});

// Shoots Tests
test('admin can view shoots list', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    Shoot::factory()->count(3)->create();

    $this->actingAs($admin)
        ->get('/admin/shoots')
        ->assertSuccessful();
});

test('admin can create shoot', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $this->actingAs($admin)
        ->get('/admin/shoots/create')
        ->assertSuccessful();

    $response = $this->actingAs($admin)->post('/admin/shoots', [
        'date' => now()->addDays(7)->format('Y-m-d'),
        'location' => 'Hall',
        'description' => 'Test shoot',
    ]);

    $response->assertRedirect();
    expect(Shoot::where('description', 'Test shoot')->exists())->toBeTrue();
});

test('admin can edit shoot', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $shoot = Shoot::factory()->create();

    $this->actingAs($admin)
        ->get("/admin/shoots/{$shoot->id}/edit")
        ->assertSuccessful();

    $response = $this->actingAs($admin)->put("/admin/shoots/{$shoot->id}", [
        'date' => $shoot->date->format('Y-m-d'),
        'location' => 'Meadow',
        'description' => 'Updated description',
    ]);

    $response->assertRedirect();
    expect($shoot->fresh()->description)->toBe('Updated description');
});

// Events Tests
test('admin can view events list', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    Event::factory()->count(3)->create();

    $this->actingAs($admin)
        ->get('/admin/events')
        ->assertSuccessful();
});

test('admin can create event', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $this->actingAs($admin)
        ->get('/admin/events/create')
        ->assertSuccessful();

    $response = $this->actingAs($admin)->post('/admin/events', [
        'title' => 'Test Event',
        'description' => 'Event description',
        'start_date' => now()->addDays(14)->format('Y-m-d\TH:i'),
        'location' => 'Club House',
        'published' => true,
    ]);

    $response->assertRedirect();
    expect(Event::where('title', 'Test Event')->exists())->toBeTrue();
});

test('admin can edit event', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $event = Event::factory()->create();

    $this->actingAs($admin)
        ->get("/admin/events/{$event->id}/edit")
        ->assertSuccessful();

    $response = $this->actingAs($admin)->put("/admin/events/{$event->id}", [
        'title' => 'Updated Event Title',
        'description' => $event->description,
        'start_date' => $event->start_date->format('Y-m-d\TH:i'),
        'published' => true,
    ]);

    $response->assertRedirect();
    expect($event->fresh()->title)->toBe('Updated Event Title');
});

// News Tests
test('admin can view news list', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    News::factory()->count(3)->create();

    $this->actingAs($admin)
        ->get('/admin/news')
        ->assertSuccessful();
});

test('admin can create news article', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $this->actingAs($admin)
        ->get('/admin/news/create')
        ->assertSuccessful();

    $response = $this->actingAs($admin)->post('/admin/news', [
        'title' => 'Test News Article',
        'content' => 'This is the news content.',
        'summary' => 'Short summary',
        'published' => true,
    ]);

    $response->assertRedirect();
    expect(News::where('title', 'Test News Article')->exists())->toBeTrue();
});

test('admin can edit news article', function () {
    $admin = User::factory()->create(['is_active' => true]);
    $admin->assignRole('Admin');

    $news = News::factory()->create();

    $this->actingAs($admin)
        ->get("/admin/news/{$news->id}/edit")
        ->assertSuccessful();

    $response = $this->actingAs($admin)->put("/admin/news/{$news->id}", [
        'title' => 'Updated News Title',
        'content' => $news->content,
        'published' => true,
    ]);

    $response->assertRedirect();
    expect($news->fresh()->title)->toBe('Updated News Title');
});
