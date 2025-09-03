from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

def create_tenant_001_pdf():
    """テナント001用の会社文書PDFを作成"""
    filename = "tenant_001_text_doc.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # ページ1: 会社概要
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height - 1*inch, "Tenant 001 Corporation Manual")
    
    c.setFont("Helvetica", 12)
    y_position = height - 1.5*inch
    
    c.drawString(1*inch, y_position, "Company Overview:")
    y_position -= 0.3*inch
    c.drawString(1.2*inch, y_position, "- Founded: 2020")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "- Industry: Cloud Computing Services")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "- Employees: 500+")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "- Headquarters: Tokyo, Japan")
    
    y_position -= 0.5*inch
    c.drawString(1*inch, y_position, "Mission Statement:")
    y_position -= 0.3*inch
    c.drawString(1.2*inch, y_position, "To provide cutting-edge cloud infrastructure solutions")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "that empower businesses to scale efficiently.")
    
    # ページ2: 製品情報
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1*inch, height - 1*inch, "Product Portfolio")
    
    c.setFont("Helvetica", 12)
    y_position = height - 1.5*inch
    
    c.drawString(1*inch, y_position, "1. CloudSync Pro")
    y_position -= 0.3*inch
    c.drawString(1.2*inch, y_position, "Enterprise-grade data synchronization platform")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "Features: Real-time sync, 99.99% uptime SLA")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "Price: Starting from $999/month")
    
    y_position -= 0.4*inch
    c.drawString(1*inch, y_position, "2. SecureVault")
    y_position -= 0.3*inch
    c.drawString(1.2*inch, y_position, "Military-grade encrypted storage solution")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "Features: AES-256 encryption, compliance ready")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "Price: Starting from $1,499/month")
    
    # ページ3: サポート手順
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1*inch, height - 1*inch, "Customer Support Procedures")
    
    c.setFont("Helvetica", 12)
    y_position = height - 1.5*inch
    
    c.drawString(1*inch, y_position, "Technical Support Process:")
    y_position -= 0.3*inch
    c.drawString(1.2*inch, y_position, "Step 1: Log into support.tenant001.com")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "Step 2: Click 'Create New Ticket'")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "Step 3: Select priority level (Critical/High/Medium/Low)")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "Step 4: Describe the issue with error logs")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "Step 5: Submit and receive ticket ID")
    
    y_position -= 0.4*inch
    c.drawString(1*inch, y_position, "Emergency Contact:")
    y_position -= 0.3*inch
    c.drawString(1.2*inch, y_position, "24/7 Hotline: +81-3-1234-5678")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "Email: emergency@tenant001.com")
    
    c.save()
    print(f"Created {filename}")

def create_tenant_002_pdf():
    """テナント002用の会社文書PDFを作成"""
    filename = "tenant_002_text_doc.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # ページ1: 会社概要
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height - 1*inch, "Tenant 002 Industries Documentation")
    
    c.setFont("Helvetica", 12)
    y_position = height - 1.5*inch
    
    c.drawString(1*inch, y_position, "Organization Profile:")
    y_position -= 0.3*inch
    c.drawString(1.2*inch, y_position, "- Established: 2018")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "- Sector: AI and Machine Learning")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "- Team Size: 200+")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "- Main Office: San Francisco, USA")
    
    y_position -= 0.5*inch
    c.drawString(1*inch, y_position, "Vision:")
    y_position -= 0.3*inch
    c.drawString(1.2*inch, y_position, "Leading the AI revolution with ethical and")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "responsible artificial intelligence solutions.")
    
    # ページ2: サービス
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1*inch, height - 1*inch, "Service Offerings")
    
    c.setFont("Helvetica", 12)
    y_position = height - 1.5*inch
    
    c.drawString(1*inch, y_position, "1. AIAnalyzer Premium")
    y_position -= 0.3*inch
    c.drawString(1.2*inch, y_position, "Advanced predictive analytics platform")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "Capabilities: Pattern recognition, trend forecasting")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "Pricing: $2,500/month per workspace")
    
    y_position -= 0.4*inch
    c.drawString(1*inch, y_position, "2. NeuralNet Builder")
    y_position -= 0.3*inch
    c.drawString(1.2*inch, y_position, "No-code neural network development tool")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "Features: Drag-and-drop interface, AutoML")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "Pricing: $3,000/month unlimited users")
    
    # ページ3: 操作手順
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1*inch, height - 1*inch, "Platform Operation Guidelines")
    
    c.setFont("Helvetica", 12)
    y_position = height - 1.5*inch
    
    c.drawString(1*inch, y_position, "Model Deployment Process:")
    y_position -= 0.3*inch
    c.drawString(1.2*inch, y_position, "1. Navigate to dashboard.tenant002.ai")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "2. Select 'Deploy New Model'")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "3. Upload model file (.h5, .pkl, or .onnx)")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "4. Configure endpoint settings")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "5. Set scaling parameters (min: 1, max: 10)")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "6. Click 'Deploy' and wait for confirmation")
    
    y_position -= 0.4*inch
    c.drawString(1*inch, y_position, "Support Channels:")
    y_position -= 0.3*inch
    c.drawString(1.2*inch, y_position, "Slack: tenant002-support.slack.com")
    y_position -= 0.2*inch
    c.drawString(1.2*inch, y_position, "Email: help@tenant002.ai")
    
    c.save()
    print(f"Created {filename}")

if __name__ == "__main__":
    create_tenant_001_pdf()
    create_tenant_002_pdf()
    print("\nText-based PDFs created successfully!")