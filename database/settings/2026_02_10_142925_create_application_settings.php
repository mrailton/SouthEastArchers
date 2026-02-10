<?php

use Spatie\LaravelSettings\Migrations\SettingsMigration;

return new class () extends SettingsMigration {
    public function up(): void
    {
        $this->migrator->add('application.membership_year_start_month', 3);
        $this->migrator->add('application.membership_year_start_day', 1);
        $this->migrator->add('application.annual_membership_cost', 10000);
        $this->migrator->add('application.membership_shoots_included', 20);
        $this->migrator->add('application.additional_shoot_cost', 500);
    }
};
