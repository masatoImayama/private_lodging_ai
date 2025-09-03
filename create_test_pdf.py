from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def create_test_pdf(filename="test_document.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Page 1
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height - 1*inch, "Private Lodging Manual")
    
    c.setFont("Helvetica", 12)
    c.drawString(1*inch, height - 1.5*inch, "Chapter 1: Reservation Process")
    
    c.setFont("Helvetica", 10)
    text1 = [
        "The reservation process for private lodging facilities follows a structured approach.",
        "First, guests must submit their booking request through the online portal.",
        "The request should include check-in date, check-out date, number of guests,",
        "and any special requirements or preferences.",
        "",
        "Upon receiving the request, the system automatically checks availability",
        "and sends a confirmation email within 24 hours. If the requested dates",
        "are not available, alternative dates will be suggested.",
        "",
        "Payment must be completed within 48 hours of confirmation to secure the booking.",
        "Accepted payment methods include credit cards, bank transfers, and digital wallets."
    ]
    
    y_position = height - 2*inch
    for line in text1:
        c.drawString(1*inch, y_position, line)
        y_position -= 15
    
    c.showPage()
    
    # Page 2
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1*inch, height - 1*inch, "Chapter 2: Check-in Procedures")
    
    c.setFont("Helvetica", 10)
    text2 = [
        "Check-in time is typically from 3:00 PM to 8:00 PM unless otherwise specified.",
        "Guests must present a valid government-issued ID upon arrival.",
        "",
        "The check-in process includes:",
        "1. Identity verification and registration",
        "2. Room key or access code distribution",
        "3. Facility orientation and rules explanation",
        "4. Emergency contact information exchange",
        "5. Wi-Fi password and amenities information",
        "",
        "Late check-in (after 8:00 PM) must be arranged in advance.",
        "Additional fees may apply for late check-in services.",
        "",
        "Early check-in is subject to availability and may incur extra charges.",
        "Guests are advised to contact the property at least 24 hours before arrival",
        "if they require early or late check-in."
    ]
    
    y_position = height - 1.5*inch
    for line in text2:
        c.drawString(1*inch, y_position, line)
        y_position -= 15
    
    c.showPage()
    
    # Page 3
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1*inch, height - 1*inch, "Chapter 3: House Rules and Regulations")
    
    c.setFont("Helvetica", 10)
    text3 = [
        "All guests must comply with the following house rules:",
        "",
        "1. Quiet hours are from 10:00 PM to 7:00 AM",
        "2. Smoking is strictly prohibited inside the building",
        "3. Pets are not allowed unless specifically approved",
        "4. Maximum occupancy limits must be respected",
        "5. Visitors must be registered at the front desk",
        "6. Damage to property will result in additional charges",
        "",
        "Kitchen Usage:",
        "- Clean all dishes and utensils after use",
        "- Do not leave food in common areas",
        "- Dispose of garbage in designated bins",
        "",
        "Safety and Security:",
        "- Lock doors and windows when leaving the room",
        "- Report any suspicious activities immediately",
        "- Keep emergency exits clear at all times"
    ]
    
    y_position = height - 1.5*inch
    for line in text3:
        c.drawString(1*inch, y_position, line)
        y_position -= 15
    
    c.showPage()
    
    # Page 4
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1*inch, height - 1*inch, "Chapter 4: Cancellation Policy")
    
    c.setFont("Helvetica", 10)
    text4 = [
        "Our cancellation policy is designed to be fair to both guests and property owners.",
        "",
        "Standard Cancellation Terms:",
        "- 30+ days before check-in: Full refund",
        "- 14-29 days before check-in: 50% refund",
        "- 7-13 days before check-in: 25% refund",
        "- Less than 7 days: No refund",
        "",
        "Exceptions may apply in cases of:",
        "- Medical emergencies (with documentation)",
        "- Natural disasters affecting travel",
        "- Government-imposed travel restrictions",
        "",
        "To cancel a reservation, guests must:",
        "1. Log into their account on the booking platform",
        "2. Navigate to 'My Reservations'",
        "3. Select the booking to cancel",
        "4. Follow the cancellation process",
        "5. Receive confirmation email within 24 hours"
    ]
    
    y_position = height - 1.5*inch
    for line in text4:
        c.drawString(1*inch, y_position, line)
        y_position -= 15
    
    c.save()
    print(f"PDF created: {filename}")

if __name__ == "__main__":
    create_test_pdf()