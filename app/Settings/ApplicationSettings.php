<?php

namespace App\Settings;

use Spatie\LaravelSettings\Settings;

class ApplicationSettings extends Settings
{
    public int $membership_year_start_month = 3;

    public int $membership_year_start_day = 1;

    public int $annual_membership_cost = 10000;

    public int $membership_shoots_included = 20;

    public int $additional_shoot_cost = 500;

    public static function group(): string
    {
        return 'application';
    }
}
