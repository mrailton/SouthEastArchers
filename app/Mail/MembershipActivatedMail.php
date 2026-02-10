<?php

namespace App\Mail;

use App\Models\Membership;
use App\Models\User;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Mail\Mailable;
use Illuminate\Mail\Mailables\Content;
use Illuminate\Mail\Mailables\Envelope;
use Illuminate\Queue\SerializesModels;

class MembershipActivatedMail extends Mailable implements ShouldQueue
{
    use Queueable;
    use SerializesModels;

    public function __construct(
        public User $user,
        public Membership $membership,
    ) {
    }

    public function envelope(): Envelope
    {
        return new Envelope(
            subject: 'Your Membership is Now Active - South East Archers',
        );
    }

    public function content(): Content
    {
        return new Content(
            view: 'emails.membership-activated',
        );
    }

    /**
     * @return array<int, \Illuminate\Mail\Mailables\Attachment>
     */
    public function attachments(): array
    {
        return [];
    }
}
