<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Account Activated - South East Archers</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <img src="{{ asset('images/logo.jpeg') }}" alt="South East Archers" style="max-width: 150px;">
    </div>
    
    <h1 style="color: #158b84; text-align: center;">Your Account is Now Active!</h1>
    
    <p>Dear {{ $user->name }},</p>
    
    <p>Great news! Your South East Archers account has been activated by an administrator.</p>
    
    <p>You can now log in to your account and access all member features:</p>
    
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{ route('login') }}" style="background-color: #158b84; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Log In Now</a>
    </div>
    
    <p>Once logged in, you can:</p>
    
    <ul>
        <li>View your dashboard and membership status</li>
        <li>Check your shoot credits</li>
        <li>View upcoming events</li>
        <li>Purchase membership or additional credits</li>
    </ul>
    
    <p>We look forward to seeing you at the range!</p>
    
    <p>Best regards,<br>
    <strong>South East Archers Team</strong></p>
    
    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
    
    <p style="font-size: 12px; color: #666; text-align: center;">
        This email was sent from South East Archers.
    </p>
</body>
</html>
