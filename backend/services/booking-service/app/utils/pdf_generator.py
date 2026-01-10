from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from datetime import datetime

def generate_receipt_pdf(booking_data: dict) -> bytes:
    """
    Generate a PDF receipt for a booking.
    booking_data expected keys:
    - booking_id
    - ride_id
    - amount (float/decimal)
    - currency (str)
    - date (datetime or str)
    - pickup_address
    - dropoff_address
    - status
    - passenger_name (optional)
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = styles["Heading1"]
    title_style.alignment = 1 # Center
    story.append(Paragraph("RideShare Receipt", title_style))
    story.append(Spacer(1, 20))

    # Details Table
    data = [
        ["Receipt Details", ""],
        ["Date", str(booking_data.get("date", datetime.now().date()))],
        ["Booking ID", str(booking_data.get("booking_id", "N/A"))],
        ["Ride ID", str(booking_data.get("ride_id", "N/A"))],
        ["Passenger", booking_data.get("passenger_name", "Valued Customer")],
        ["Status", booking_data.get("status", "COMPLETED").upper()],
        ["", ""],
        ["Route Information", ""],
        ["Pickup", booking_data.get("pickup_address", "N/A")],
        ["Dropoff", booking_data.get("dropoff_address", "N/A")],
        ["", ""],
        ["Payment", ""],
        ["Amount Paid", f"{booking_data.get('amount', 0.00)} {booking_data.get('currency', 'USD')}"],
    ]

    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('SPAN', (0, 0), (1, 0)), # Header span
        ('SPAN', (0, 6), (1, 6)), # Spacer
        ('SPAN', (0, 7), (1, 7)), # Route Header
        ('SPAN', (0, 10), (1, 10)), # Spacer
        ('SPAN', (0, 11), (1, 11)), # Payment Header
        ('FONTNAME', (0, 7), (-1, 7), 'Helvetica-Bold'),
        ('FONTNAME', (0, 11), (-1, 11), 'Helvetica-Bold'),
    ])

    t = Table(data, colWidths=[150, 300])
    t.setStyle(table_style)
    story.append(t)
    
    story.append(Spacer(1, 40))
    story.append(Paragraph("Thank you for riding with us!", styles["Normal"]))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
