<?php

use App\Models\Event;
use App\Models\News;

test('home page can be rendered', function () {
    $this->get('/')->assertSuccessful()->assertSee('South East Archers');
});

test('about page can be rendered', function () {
    $this->get('/about')->assertSuccessful()->assertSee('About');
});

test('events page can be rendered', function () {
    $this->get('/events')->assertSuccessful()->assertSee('Events');
});

test('events page shows published upcoming events', function () {
    Event::factory()->create([
        'title' => 'Published Event',
        'published' => true,
        'start_date' => now()->addDays(7),
    ]);
    Event::factory()->create([
        'title' => 'Unpublished Event',
        'published' => false,
        'start_date' => now()->addDays(7),
    ]);

    $response = $this->get('/events');

    $response->assertSuccessful()
        ->assertSee('Published Event')
        ->assertDontSee('Unpublished Event');
});

test('membership info page can be rendered', function () {
    $this->get('/membership')->assertSuccessful()->assertSee('Membership');
});

test('news listing page can be rendered', function () {
    $this->get('/news')->assertSuccessful()->assertSee('News');
});

test('news listing shows published articles', function () {
    News::factory()->create([
        'title' => 'Published Article',
        'published' => true,
    ]);
    News::factory()->create([
        'title' => 'Unpublished Article',
        'published' => false,
    ]);

    $response = $this->get('/news');

    $response->assertSuccessful()
        ->assertSee('Published Article')
        ->assertDontSee('Unpublished Article');
});

test('news detail page can be rendered for published article', function () {
    $news = News::factory()->create([
        'title' => 'Test Article Title',
        'content' => 'Test article content goes here.',
        'published' => true,
    ]);

    $response = $this->get("/news/{$news->id}");

    $response->assertSuccessful()
        ->assertSee('Test Article Title')
        ->assertSee('Test article content goes here.');
});

test('news detail page returns 404 for unpublished article', function () {
    $news = News::factory()->create(['published' => false]);

    $this->get("/news/{$news->id}")->assertNotFound();
});
