<?php

namespace App\Enums;

enum PaymentType: string
{
    case Membership = 'membership';
    case Credits = 'credits';
}
