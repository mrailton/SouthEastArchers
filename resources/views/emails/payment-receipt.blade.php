<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Payment Receipt - South East Archers</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <img src="{{ asset('images/logo.jpeg') }}" alt="South East Archers" style="max-width: 150px;">
    </div>
    
    <h1 style="color: #158b84; text-align: center;">Payment Receipt</h1>
    
    <p>Dear {{ $user->name }},</p>
    
    <p>Thank you for your payment. Here are your transaction details:</p>
    
    <div style="background-color: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0;">
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 10px 0; border-bottom: 1px solid #ddd;"><strong>Date:</strong></td>
                <td style="padding: 10px 0; border-bottom: 1px solid #ddd; text-align: right;">{{ $payment->created_at->format('d M Y, H:i') }}</td>
            </tr>
            <tr>
                <td style="padding: 10px 0; border-bottom: 1px solid #ddd;"><strong>Description:</strong></td>
                <td style="padding: 10px 0; border-bottom: 1px solid #ddd; text-align: right;">{{ $payment->description }}</td>
            </tr>
            <tr>
                <td style="padding: 10px 0; border-bottom: 1px solid #ddd;"><strong>Payment Method:</strong></td>
                <td style="padding: 10px 0; border-bottom: 1px solid #ddd; text-align: right;">{{ ucfirst($payment->payment_method->value) }}</td>
            </tr>
            <tr>
                <td style="padding: 10px 0;"><strong>Amount:</strong></td>
                <td style="padding: 10px 0; text-align: right; font-size: 18px; color: #158b84;"><strong>€{{ number_format($payment->amount_cents / 100, 2) }}</strong></td>
            </tr>
        </table>
    </div>
    
    @if($payment->external_transaction_id)
    <p><strong>Transaction ID:</strong> {{ $payment->external_transaction_id }}</p>
    @endif
    
    <p>You can view your payment history in your <a href="{{ route('payment.history') }}" style="color: #158b84;">member dashboard</a>.</p>
    
    <p>Thank you for your continued support!</p>
    
    <p>Best regards,<br>
    <strong>South East Archers Team</strong></p>
    
    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
    
    <p style="font-size: 12px; color: #666; text-align: center;">
        This is your payment receipt from South East Archers. Please keep this for your records.
    </p>
</body>
</html>
