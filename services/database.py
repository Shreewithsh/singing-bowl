"""
Singing Bowl Export Desk
Database Configuration
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Initialize the database with the Flask app."""
    db.init_app(app)
    with app.app_context():
        from services.models import Lead, Campaign, Settings
        db.create_all()
        _seed_default_settings()


def _seed_default_settings():
    """Seed default settings if not present."""
    from services.models import Settings
    defaults = {
        'mail_server': 'smtp.gmail.com',
        'mail_port': '587',
        'mail_use_tls': 'true',
        'mail_username': '',
        'mail_password': '',
        'serpapi_key': '',
        'google_delay': '2',
        'max_pages': '5',
        'whatsapp_number': '+977-9800000000',
        'product_catalog_pdf': 'https://yourdomain.com/catalog.pdf',
        'unsubscribe_url': 'https://yourdomain.com/unsubscribe',
        'email_subject': 'Handcrafted Singing Bowl Export Catalog',
        'email_body': _default_email_body()
    }
    for key, value in defaults.items():
        existing = Settings.query.filter_by(key=key).first()
        if not existing:
            s = Settings(key=key, value=value)
            from services.database import db
            db.session.add(s)
    db.session.commit()


def _default_email_body():
    return """<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
  <div style="background: linear-gradient(135deg, #16A34A, #15803d); padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 24px;">
    <h1 style="color: white; margin: 0; font-size: 28px;">🎵 Himalayan Singing Bowls</h1>
    <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0;">Premium Export Catalog 2024</p>
  </div>
  
  <p>Dear {{ownerName}},</p>
  
  <p>I hope this message finds you well. My name is [Your Name] from <strong>[Your Company]</strong>, a leading exporter of authentic, handcrafted Himalayan singing bowls and wellness products directly from Nepal.</p>
  
  <p>We noticed that <strong>{{businessName}}</strong> serves customers in <strong>{{country}}</strong> who appreciate quality wellness and spiritual products. We believe our singing bowls would be an excellent addition to your product offerings.</p>
  
  <h3 style="color: #16A34A;">Why Partner With Us?</h3>
  <ul>
    <li>✅ 100% handcrafted by Nepali artisans with 3+ generations of experience</li>
    <li>✅ Premium 7-metal alloy bowls with rich, sustained resonance</li>
    <li>✅ Wholesale pricing with flexible MOQ from 10 pieces</li>
    <li>✅ Custom branding and packaging available</li>
    <li>✅ Worldwide shipping with full insurance coverage</li>
    <li>✅ Certificate of Authenticity included</li>
  </ul>
  
  <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 16px; margin: 20px 0;">
    <p style="margin: 0; font-weight: bold; color: #16A34A;">📦 Download Our Export Catalog</p>
    <p style="margin: 8px 0 0 0;"><a href="{{productCatalogPDF}}" style="color: #16A34A;">Click here to view our full product catalog →</a></p>
  </div>
  
  <p>I would love to discuss how we can create a mutually beneficial partnership. You can also reach us directly on WhatsApp: <strong>{{whatsAppNumber}}</strong></p>
  
  <p>Visit our website: <a href="{{website}}" style="color: #16A34A;">{{website}}</a></p>
  
  <p>Looking forward to the possibility of working together!</p>
  
  <p>Warm regards,<br><strong>[Your Name]</strong><br>[Your Company]<br>Kathmandu, Nepal</p>
  
  <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
  <p style="font-size: 12px; color: #999; text-align: center;">
    To unsubscribe from our emails, <a href="{{unsubscribeUrl}}" style="color: #999;">click here</a>.
  </p>
</div>"""
