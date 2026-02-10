<?php

namespace App\Enums;

enum PaymentMethod: string
{
    case Cash = 'cash';
    case Online = 'online';
}
