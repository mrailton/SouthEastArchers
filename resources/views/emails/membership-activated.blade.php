<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Membership Activated - South East Archers</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <img src="{{ asset('images/logo.jpeg') }}" alt="South East Archers" style="max-width: 150px;">
    </div>
    
    <h1 style="color: #158b84; text-align: center;">Membership Activated!</h1>
    
    <p>Dear {{ $user->name }},</p>
    
    <p>Great news! Your South East Archers membership is now active.</p>
    
    <div style="background-color: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #158b84;">Membership Details</h3>
        <table style="width: 100%;">
            <tr>
                <td style="padding: 5px 0;"><strong>Status:</strong></td>
                <td style="padding: 5px 0; text-align: right;"><span style="background-color: #d4edda; color: #155724; padding: 3px 10px; border-radius: 3px;">Active</span></td>
            </tr>
            <tr>
                <td style="padding: 5px 0;"><strong>Start Date:</strong></td>
                <td style="padding: 5px 0; text-align: right;">{{ $membership->start_date->format('d M Y') }}</td>
            </tr>
            <tr>
                <td style="padding: 5px 0;"><strong>Expiry Date:</strong></td>
                <td style="padding: 5px 0; text-align: right;">{{ $membership->expiry_date->format('d M Y') }}</td>
            </tr>
            <tr>
                <td style="padding: 5px 0;"><strong>Included Shoots:</strong></td>
                <td style="padding: 5px 0; text-align: right;">{{ $membership->initial_credits }}</td>
            </tr>
        </table>
    </div>
    
    <p>With your membership, you can:</p>
    
    <ul>
        <li>Attend shoots at our club (use your included credits)</li>
        <li>Participate in club events</li>
        <li>Purchase additional shoot credits if needed</li>
        <li>Access exclusive member resources</li>
    </ul>
    
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{ route('dashboard') }}" style="background-color: #158b84; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">View Your Dashboard</a>
    </div>
    
    <p>We look forward to seeing you at the range!</p>
    
    <p>Best regards,<br>
    <strong>South East Archers Team</strong></p>
    
    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
    
    <p style="font-size: 12px; color: #666; text-align: center;">
        This email was sent from South East Archers.
    </p>
</body>
</html>
