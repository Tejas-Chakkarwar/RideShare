"""
Email templates for booking notifications.
"""
from typing import Dict, Any
from jinja2 import Template

def render_booking_created_passenger(data: Dict[str, Any]) -> str:
    """Render booking confirmation email for passenger."""
    template = Template("""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #0066cc; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }
        .content { background: #f9f9f9; padding: 20px; }
        .ride-details { background: white; padding: 15px; margin: 20px 0; border-left: 4px solid #0066cc; }
        .ride-details p { margin: 8px 0; }
        .footer { background: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; color: #666; }
        .status-badge { display: inline-block; background: #ffc107; color: #000; padding: 5px 10px; border-radius: 3px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚗 SJSU RideShare</h1>
            <p>Booking Confirmation</p>
        </div>
        
        <div class="content">
            <h2>Hi {{ passenger_name }}! 👋</h2>
            <p>Your ride request has been submitted and is <span class="status-badge">PENDING</span> driver approval.</p>
            
            <div class="ride-details">
                <h3>📍 Ride Details</h3>
                <p><strong>From:</strong> {{ origin }}</p>
                <p><strong>To:</strong> {{ destination }}</p>
                <p><strong>Departure:</strong> {{ departure_time }}</p>
                <p><strong>Seats Requested:</strong> {{ seats_booked }}</p>
                <p><strong>Total Amount:</strong> ${{ total_amount }}</p>
                <p><strong>Booking ID:</strong> {{ booking_id }}</p>
            </div>
            
            <p><strong>What's Next?</strong></p>
            <ul>
                <li>The driver will review your request</li>
                <li>You'll receive an email when it's approved or rejected</li>
                <li>Check the app for real-time updates</li>
            </ul>
            
            {% if passenger_notes %}
            <p><strong>Your Message to Driver:</strong><br>"{{ passenger_notes }}"</p>
            {% endif %}
        </div>
        
        <div class="footer">
            <p>SJSU RideShare - Safe Carpooling for Students</p>
            <p>Need help? Contact support@sjsurideshare.com</p>
        </div>
    </div>
</body>
</html>
    """)
    return template.render(**data)


def render_booking_created_driver(data: Dict[str, Any]) -> str:
    """Render new booking notification for driver."""
    template = Template("""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #0066cc; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }
        .content { background: #f9f9f9; padding: 20px; }
        .passenger-info { background: #e8f4fd; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .ride-details { background: white; padding: 15px; margin: 20px 0; border-left: 4px solid #0066cc; }
        .actions { text-align: center; margin: 30px 0; }
        .btn { display: inline-block; padding: 12px 30px; margin: 0 10px; text-decoration: none; border-radius: 5px; font-weight: bold; }
        .btn-approve { background: #28a745; color: white; }
        .btn-reject { background: #dc3545; color: white; }
        .footer { background: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚗 SJSU RideShare</h1>
            <p>New Ride Request!</p>
        </div>
        
        <div class="content">
            <h2>Hi {{ driver_name }}! 👋</h2>
            <p><strong>{{ passenger_name }}</strong> wants to join your ride.</p>
            
            <div class="passenger-info">
                <h3>👤 Passenger Info</h3>
                <p><strong>Name:</strong> {{ passenger_name }}</p>
                <p><strong>Seats Needed:</strong> {{ seats_booked }}</p>
                {% if passenger_notes %}
                <p><strong>Message:</strong> "{{ passenger_notes }}"</p>
                {% endif %}
            </div>
            
            <div class="ride-details">
                <h3>📍 Your Ride</h3>
                <p><strong>Route:</strong> {{ origin }} → {{ destination }}</p>
                <p><strong>Departure:</strong> {{ departure_time }}</p>
                <p><strong>They'll Pay:</strong> ${{ total_amount }}</p>
            </div>
            
            <div class="actions">
                <a href="{{ app_url }}/bookings/{{ booking_id }}/approve" class="btn btn-approve">✅ Approve</a>
                <a href="{{ app_url }}/bookings/{{ booking_id }}/reject" class="btn btn-reject">❌ Reject</a>
            </div>
            
            <p style="text-align: center; color: #666; font-size: 14px;">
                Or manage this request in the SJSU RideShare app
            </p>
        </div>
        
        <div class="footer">
            <p>SJSU RideShare - Safe Carpooling for Students</p>
        </div>
    </div>
</body>
</html>
    """)
    return template.render(**data)


def render_booking_approved(data: Dict[str, Any]) -> str:
    """Render booking approved email for passenger."""
    template = Template("""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #28a745; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }
        .content { background: #f9f9f9; padding: 20px; }
        .success-banner { background: #d4edda; border: 2px solid #28a745; padding: 15px; margin: 20px 0; border-radius: 5px; text-align: center; }
        .ride-details { background: white; padding: 15px; margin: 20px 0; border-left: 4px solid #28a745; }
        .footer { background: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Great News!</h1>
        </div>
        
        <div class="content">
            <div class="success-banner">
                <h2 style="margin: 0; color: #155724;">✅ Your Ride is Confirmed!</h2>
            </div>
            
            <p>Hi {{ passenger_name }}!</p>
            <p><strong>{{ driver_name }}</strong> has approved your booking request. You're all set for your ride!</p>
            
            <div class="ride-details">
                <h3>📍 Ride Details</h3>
                <p><strong>Driver:</strong> {{ driver_name }}</p>
                <p><strong>From:</strong> {{ origin }}</p>
                <p><strong>To:</strong> {{ destination }}</p>
                <p><strong>Departure:</strong> {{ departure_time }}</p>
                <p><strong>Seats:</strong> {{ seats_booked }}</p>
                <p><strong>Total:</strong> ${{ total_amount }}</p>
            </div>
            
            <p><strong>Important Reminders:</strong></p>
            <ul>
                <li>Be on time at the pickup location</li>
                <li>Bring exact change or ensure payment is processed</li>
                <li>Contact your driver if you need to cancel</li>
                <li>Rate your experience after the ride!</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>Have a safe trip! 🚗</p>
            <p>SJSU RideShare - Safe Carpooling for Students</p>
        </div>
    </div>
</body>
</html>
    """)
    return template.render(**data)


def render_booking_rejected(data: Dict[str, Any]) -> str:
    """Render booking rejected email for passenger."""
    template = Template("""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #dc3545; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }
        .content { background: #f9f9f9; padding: 20px; }
        .info-box { background: #fff3cd; border: 2px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .footer { background: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SJSU RideShare</h1>
            <p>Booking Update</p>
        </div>
        
        <div class="content">
            <p>Hi {{ passenger_name }},</p>
            <p>Unfortunately, your ride request was not approved by the driver.</p>
            
            <div class="info-box">
                <p><strong>📍 Route:</strong> {{ origin }} → {{ destination }}</p>
                <p><strong>🕐 Time:</strong> {{ departure_time }}</p>
                <p><strong>💺 Seats:</strong> {{ seats_booked }}</p>
            </div>
            
            <p><strong>What you can do:</strong></p>
            <ul>
                <li>Search for other available rides on the same route</li>
                <li>Try booking with a different driver</li>
                <li>Adjust your departure time for more options</li>
            </ul>
            
            <p>Your reserved seats have been released and no charges were made.</p>
        </div>
        
        <div class="footer">
            <p>Keep looking - there are plenty of rides available!</p>
            <p>SJSU RideShare - Safe Carpooling for Students</p>
        </div>
    </div>
</body>
</html>
    """)
    return template.render(**data)
