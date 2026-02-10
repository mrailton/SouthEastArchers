<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to South East Archers</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <img src="{{ asset('images/logo.jpeg') }}" alt="South East Archers" style="max-width: 150px;">
    </div>
    
    <h1 style="color: #158b84; text-align: center;">Welcome to South East Archers!</h1>
    
    <p>Dear {{ $user->name }},</p>
    
    <p>Thank you for registering with South East Archers. We're excited to have you join our archery community!</p>
    
    <p>Your account has been created successfully. Please note that your account will need to be activated by an administrator before you can log in.</p>
    
    <p>Once your account is activated, you'll receive another email and will be able to:</p>
    
    <ul>
        <li>Access your member dashboard</li>
        <li>View upcoming shoots and events</li>
        <li>Manage your membership and credits</li>
        <li>Connect with other club members</li>
    </ul>
    
    <p>If you have any questions, please don't hesitate to contact us.</p>
    
    <p>Best regards,<br>
    <strong>South East Archers Team</strong></p>
    
    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
    
    <p style="font-size: 12px; color: #666; text-align: center;">
        This email was sent from South East Archers. If you didn't register for an account, please ignore this email.
    </p>
</body>
</html>
