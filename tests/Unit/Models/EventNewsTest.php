<?php

use App\Models\Event;
use App\Models\News;

test('event can be created', function () {
    $event = Event::create([
        'title' => 'Test Event',
        'description' => 'Event description',
        'start_date' => now()->addDays(7),
        'published' => true,
    ]);

    expect($event)->not->toBeNull()
        ->and($event->title)->toBe('Test Event');
});

test('event isUpcoming returns true for future events', function () {
    $event = Event::create([
        'title' => 'Future Event',
        'description' => 'Description',
        'start_date' => now()->addDays(7),
        'published' => true,
    ]);

    expect($event->isUpcoming())->toBeTrue();
});

test('event isUpcoming returns false for past events', function () {
    $event = Event::create([
        'title' => 'Past Event',
        'description' => 'Description',
        'start_date' => now()->subDays(7),
        'published' => true,
    ]);

    expect($event->isUpcoming())->toBeFalse();
});

test('event publish sets published to true', function () {
    $event = Event::create([
        'title' => 'Draft Event',
        'description' => 'Description',
        'start_date' => now()->addDays(7),
        'published' => false,
    ]);

    $event->publish();

    expect($event->published)->toBeTrue();
});

test('news can be created', function () {
    $news = News::create([
        'title' => 'Test News',
        'content' => 'News content here',
        'published' => true,
    ]);

    expect($news)->not->toBeNull()
        ->and($news->title)->toBe('Test News');
});

test('news publish sets published to true and published_at', function () {
    $news = News::create([
        'title' => 'Draft News',
        'content' => 'Content',
        'published' => false,
    ]);

    $news->publish();

    expect($news->published)->toBeTrue()
        ->and($news->published_at)->not->toBeNull();
});
