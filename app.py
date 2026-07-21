"""
Singing Bowl Export Desk
Main Flask Application
"""
import csv
import io
import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta
from functools import wraps

import pandas as pd
from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, jsonify, redirect,
    url_for, flash, send_file, Response, stream_with_context
)
from sqlalchemy import func

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ─── App Factory ──────────────────────────────────────────────────────────────

def create_app():
    app = Flask(__name__)

    # Config
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'singing-bowl-desk-secret-2024')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB upload limit

    # Create required dirs
    os.makedirs('instance', exist_ok=True)
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('static/exports', exist_ok=True)

    # Initialize DB
    from services.database import init_db
    init_db(app)

    return app


app = create_app()

# Import after app creation to avoid circular imports
from services.database import db
from services.models import Lead, Campaign, Settings
from services.search_service import simulate_serpapi_search, get_seed_urls_from_text
from services.scraper import scrape_from_search_results
from services.email_sender import run_bulk_email_campaign, personalize_email, test_smtp_connection
from services.utils import validate_email, calculate_score

# ─── Global State for Background Jobs ─────────────────────────────────────────

search_job_state = {
    'running': False,
    'progress': 0,
    'total': 0,
    'message': '',
    'results': None,
    'error': None
}

email_job_state = {
    'running': False,
    'current': 0,
    'total': 0,
    'current_email': '',
    'sent': 0,
    'failed': 0,
    'skipped': 0,
    'completed': False,
    'error': None,
    'campaign_id': None
}


# ─── Context Processors ───────────────────────────────────────────────────────

@app.context_processor
def inject_stats():
    """Inject global stats into all templates."""
    try:
        total = Lead.query.count()
        contacted = Lead.query.filter_by(contacted=True).count()
        emails_sent = Lead.query.filter_by(email_status='sent').count()
        emails_failed = Lead.query.filter_by(email_status='failed').count()
        sender_email = Settings.get('mail_username', 'Not configured')
    except Exception:
        total = contacted = emails_sent = emails_failed = 0
        sender_email = 'Not configured'

    return dict(
        global_stats={
            'total': total,
            'contacted': contacted,
            'emails_sent': emails_sent,
            'emails_failed': emails_failed,
        },
        sender_email=sender_email,
        now=datetime.utcnow()
    )


# ─── Routes: Dashboard ────────────────────────────────────────────────────────

@app.route('/')
def dashboard():
    stats = {
        'total': Lead.query.count(),
        'contacted': Lead.query.filter_by(contacted=True).count(),
        'emails_sent': Lead.query.filter_by(email_status='sent').count(),
        'emails_failed': Lead.query.filter_by(email_status='failed').count(),
    }
    serpapi_key = Settings.get('serpapi_key', '')
    sender_email = Settings.get('mail_username', '')
    return render_template('dashboard.html',
                           stats=stats,
                           serpapi_configured=bool(serpapi_key and serpapi_key != 'your-serpapi-key-here'),
                           email_configured=bool(sender_email),
                           active_page='dashboard')


# ─── Routes: Lead Search ──────────────────────────────────────────────────────

@app.route('/search')
def search_page():
    return render_template('search.html', active_page='search')


@app.route('/api/search', methods=['POST'])
def api_search():
    """Start a background search job."""
    global search_job_state

    if search_job_state.get('running'):
        return jsonify({'error': 'A search is already running'}), 409

    data = request.get_json()
    keywords = data.get('keywords', 'singing bowls wholesale').strip()
    countries_raw = data.get('countries', 'USA, UK')
    countries = [c.strip() for c in countries_raw.split(',') if c.strip()]
    limit = min(int(data.get('limit', 20)), 100)
    seed_urls_text = data.get('seed_urls', '').strip()

    search_job_state = {
        'running': True,
        'progress': 0,
        'total': limit,
        'message': 'Initializing search...',
        'results': None,
        'error': None
    }

    def run_search():
        global search_job_state
        try:
            serpapi_key = Settings.get('serpapi_key', '')

            search_job_state['message'] = 'Searching for business websites...'
            search_job_state['progress'] = 5

            # Get search results
            search_results = simulate_serpapi_search(keywords, countries, limit, serpapi_key)

            # Add seed URLs if provided
            seed_urls = get_seed_urls_from_text(seed_urls_text)
            for su in seed_urls:
                search_results.append({'url': su, 'title': '', 'snippet': '', 'metadata': {}})

            search_job_state['total'] = len(search_results)
            search_job_state['message'] = f'Found {len(search_results)} websites. Extracting contacts...'
            search_job_state['progress'] = 15

            def progress_cb(current, total, msg):
                pct = 15 + int((current / max(total, 1)) * 65)
                search_job_state['progress'] = pct
                search_job_state['message'] = msg

            # Scrape websites
            extracted = scrape_from_search_results(search_results, countries, progress_cb)

            search_job_state['message'] = 'Validating and importing leads...'
            search_job_state['progress'] = 82

            # Import into DB
            imported = 0
            duplicates = 0
            for lead_data in extracted:
                email = lead_data.get('email', '').strip().lower()
                if not email or not validate_email(email):
                    continue
                # Duplicate check
                existing = Lead.query.filter_by(email=email).first()
                if existing:
                    duplicates += 1
                    continue
                new_lead = Lead(
                    business_name=lead_data.get('business_name', '')[:255],
                    owner_name=lead_data.get('owner_name', '')[:255],
                    email=email,
                    phone=lead_data.get('phone', '')[:100],
                    country=lead_data.get('country', '')[:100],
                    website=lead_data.get('website', '')[:500],
                    source_url=lead_data.get('source_url', '')[:500],
                    score=lead_data.get('score', 0),
                    contacted=False
                )
                db.session.add(new_lead)
                imported += 1

            db.session.commit()

            search_job_state['progress'] = 100
            search_job_state['message'] = 'Done!'
            search_job_state['running'] = False
            search_job_state['results'] = {
                'websites_found': len(search_results),
                'emails_extracted': len(extracted),
                'imported': imported,
                'duplicates': duplicates
            }
            logger.info(f"Search complete: {imported} leads imported, {duplicates} duplicates")

        except Exception as e:
            logger.error(f"Search job error: {e}", exc_info=True)
            search_job_state['running'] = False
            search_job_state['error'] = str(e)

    t = threading.Thread(target=run_search, daemon=True)
    t.start()
    return jsonify({'message': 'Search started', 'status': 'running'})


@app.route('/api/search/status')
def api_search_status():
    """Poll search job status."""
    return jsonify(search_job_state)


# ─── Routes: Leads ────────────────────────────────────────────────────────────

@app.route('/leads')
def leads_page():
    email_subject = Settings.get('email_subject', 'Handcrafted Singing Bowl Export Catalog')
    email_body = Settings.get('email_body', '')
    countries = db.session.query(Lead.country).filter(Lead.country != '').distinct().order_by(Lead.country).all()
    country_list = [c[0] for c in countries if c[0]]
    return render_template('leads.html',
                           active_page='leads',
                           email_subject=email_subject,
                           email_body=email_body,
                           countries=country_list)


@app.route('/api/leads')
def api_leads():
    """Get paginated leads with filters."""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 25))
    search = request.args.get('search', '').strip()
    country = request.args.get('country', '').strip()
    contacted = request.args.get('contacted', '').strip()

    query = Lead.query
    if search:
        like = f'%{search}%'
        query = query.filter(
            db.or_(
                Lead.email.ilike(like),
                Lead.business_name.ilike(like),
                Lead.owner_name.ilike(like),
                Lead.phone.ilike(like)
            )
        )
    if country:
        query = query.filter(Lead.country.ilike(f'%{country}%'))
    if contacted == 'yes':
        query = query.filter(Lead.contacted == True)
    elif contacted == 'no':
        query = query.filter(Lead.contacted == False)

    total = query.count()
    leads = query.order_by(Lead.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'leads': [l.to_dict() for l in leads.items],
        'total': total,
        'page': page,
        'pages': leads.pages,
        'per_page': per_page
    })


@app.route('/api/leads/<int:lead_id>', methods=['DELETE'])
def api_delete_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    db.session.delete(lead)
    db.session.commit()
    return jsonify({'message': 'Lead deleted'})


@app.route('/api/leads/bulk-delete', methods=['POST'])
def api_bulk_delete_leads():
    data = request.get_json()
    ids = data.get('ids', [])
    if not ids:
        return jsonify({'error': 'No IDs provided'}), 400
    Lead.query.filter(Lead.id.in_(ids)).delete(synchronize_session=False)
    db.session.commit()
    return jsonify({'message': f'Deleted {len(ids)} leads'})


@app.route('/api/leads/save-template', methods=['POST'])
def api_save_template():
    data = request.get_json()
    subject = data.get('subject', '').strip()
    body = data.get('body', '').strip()
    if subject:
        Settings.set('email_subject', subject)
    if body:
        Settings.set('email_body', body)
    return jsonify({'message': 'Template saved'})


@app.route('/api/leads/preview-email', methods=['POST'])
def api_preview_email():
    data = request.get_json()
    body = data.get('body', '')
    subject = data.get('subject', '')
    # Use first uncontacted lead as preview
    sample_lead = Lead.query.filter_by(contacted=False).first()
    if not sample_lead:
        sample_lead = Lead.query.first()

    if sample_lead:
        lead_dict = sample_lead.to_dict()
    else:
        lead_dict = {
            'owner_name': 'John Smith',
            'business_name': 'Wellness Store',
            'country': 'United States',
            'website': 'https://example.com',
            'email': 'john@example.com'
        }

    extra = {
        'product_catalog_pdf': Settings.get('product_catalog_pdf', 'https://yourdomain.com/catalog.pdf'),
        'whatsapp_number': Settings.get('whatsapp_number', '+977-9800000000'),
        'unsubscribe_url': Settings.get('unsubscribe_url', 'https://yourdomain.com/unsubscribe')
    }
    lead_dict.update(extra)

    preview_body = personalize_email(body, lead_dict)
    preview_subject = personalize_email(subject, lead_dict)
    return jsonify({'subject': preview_subject, 'body': preview_body})


@app.route('/api/leads/send-bulk', methods=['POST'])
def api_send_bulk():
    """Start bulk email campaign in background."""
    global email_job_state

    if email_job_state.get('running'):
        return jsonify({'error': 'A campaign is already running'}), 409

    data = request.get_json()
    subject = data.get('subject', Settings.get('email_subject', 'Singing Bowl Export Catalog'))
    body = data.get('body', Settings.get('email_body', ''))

    if not subject or not body:
        return jsonify({'error': 'Subject and body are required'}), 400

    smtp_config = {
        'mail_server': Settings.get('mail_server', 'smtp.gmail.com'),
        'mail_port': Settings.get('mail_port', '587'),
        'mail_use_tls': Settings.get('mail_use_tls', 'true'),
        'mail_username': Settings.get('mail_username', os.getenv('MAIL_USERNAME', '')),
        'mail_password': Settings.get('mail_password', os.getenv('MAIL_PASSWORD', '')),
    }

    if not smtp_config['mail_username']:
        return jsonify({'error': 'SMTP email not configured. Go to Settings.'}), 400

    leads = Lead.query.filter_by(contacted=False).filter(Lead.email != '').all()
    if not leads:
        return jsonify({'error': 'No uncontacted leads found'}), 400

    email_job_state = {
        'running': True,
        'current': 0,
        'total': len(leads),
        'current_email': '',
        'sent': 0,
        'failed': 0,
        'skipped': 0,
        'completed': False,
        'error': None,
        'campaign_id': None
    }

    def run_campaign():
        global email_job_state
        try:
            # Create campaign record
            campaign = Campaign(
                name=f'Campaign {datetime.utcnow().strftime("%Y-%m-%d %H:%M")}',
                subject=subject,
                body_html=body,
                status='running'
            )
            db.session.add(campaign)
            db.session.commit()
            email_job_state['campaign_id'] = campaign.id

            extra = {
                'product_catalog_pdf': Settings.get('product_catalog_pdf', ''),
                'whatsapp_number': Settings.get('whatsapp_number', ''),
                'unsubscribe_url': Settings.get('unsubscribe_url', '')
            }

            def progress_cb(state):
                email_job_state.update({
                    'current': state['current'],
                    'total': state['total'],
                    'current_email': state['email'],
                    'sent': state['sent'],
                    'failed': state['failed'],
                    'skipped': state['skipped']
                })

            delay_min = float(Settings.get('google_delay', '2'))
            delay_max = delay_min + 3

            results = run_bulk_email_campaign(
                leads=[l.to_dict() for l in leads],
                subject=subject,
                body_template=body,
                smtp_config=smtp_config,
                extra_placeholders=extra,
                delay_min=delay_min,
                delay_max=delay_max,
                progress_callback=progress_cb
            )

            # Update lead records
            for lead_id in results['sent']:
                lead = Lead.query.get(lead_id)
                if lead:
                    lead.contacted = True
                    lead.email_status = 'sent'
                    lead.last_contacted = datetime.utcnow()

            for lead_id in results['failed']:
                lead = Lead.query.get(lead_id)
                if lead:
                    lead.email_status = 'failed'

            # Update campaign
            campaign.total_sent = len(results['sent'])
            campaign.total_failed = len(results['failed'])
            campaign.total_skipped = len(results['skipped'])
            campaign.status = 'completed'
            campaign.completed_at = datetime.utcnow()
            db.session.commit()

            email_job_state.update({
                'running': False,
                'completed': True,
                'sent': len(results['sent']),
                'failed': len(results['failed']),
                'skipped': len(results['skipped'])
            })

        except Exception as e:
            logger.error(f"Campaign error: {e}", exc_info=True)
            email_job_state['running'] = False
            email_job_state['error'] = str(e)

    t = threading.Thread(target=run_campaign, daemon=True)
    t.start()
    return jsonify({'message': 'Campaign started', 'total': len(leads)})


@app.route('/api/leads/email-status')
def api_email_status():
    return jsonify(email_job_state)


@app.route('/api/leads/<int:lead_id>/send', methods=['POST'])
def api_send_single(lead_id):
    """Send email to a single lead."""
    lead = Lead.query.get_or_404(lead_id)
    data = request.get_json() or {}
    subject = data.get('subject', Settings.get('email_subject', 'Singing Bowl Export'))
    body = data.get('body', Settings.get('email_body', ''))

    smtp_config = {
        'mail_server': Settings.get('mail_server', 'smtp.gmail.com'),
        'mail_port': Settings.get('mail_port', '587'),
        'mail_use_tls': Settings.get('mail_use_tls', 'true'),
        'mail_username': Settings.get('mail_username', os.getenv('MAIL_USERNAME', '')),
        'mail_password': Settings.get('mail_password', os.getenv('MAIL_PASSWORD', '')),
    }

    if not smtp_config['mail_username']:
        return jsonify({'error': 'SMTP not configured'}), 400

    try:
        from services.email_sender import create_smtp_connection, send_single_email
        server = create_smtp_connection(smtp_config)

        lead_dict = lead.to_dict()
        lead_dict.update({
            'product_catalog_pdf': Settings.get('product_catalog_pdf', ''),
            'whatsapp_number': Settings.get('whatsapp_number', ''),
            'unsubscribe_url': Settings.get('unsubscribe_url', '')
        })

        personalized_body = personalize_email(body, lead_dict)
        personalized_subject = personalize_email(subject, lead_dict)

        success = send_single_email(
            server, smtp_config['mail_username'],
            lead.email, personalized_subject, personalized_body
        )
        server.quit()

        if success:
            lead.contacted = True
            lead.email_status = 'sent'
            lead.last_contacted = datetime.utcnow()
            db.session.commit()
            return jsonify({'message': f'Email sent to {lead.email}'})
        else:
            lead.email_status = 'failed'
            db.session.commit()
            return jsonify({'error': 'Failed to send email'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─── Routes: Reports ─────────────────────────────────────────────────────────

@app.route('/reports')
def reports_page():
    return render_template('reports.html', active_page='reports')


@app.route('/api/reports/stats')
def api_report_stats():
    total = Lead.query.count()
    contacted = Lead.query.filter_by(contacted=True).count()
    sent = Lead.query.filter_by(email_status='sent').count()
    failed = Lead.query.filter_by(email_status='failed').count()
    success_rate = round((sent / max(contacted, 1)) * 100, 1) if contacted else 0

    # Countries distribution
    country_counts = db.session.query(
        Lead.country, func.count(Lead.id).label('count')
    ).filter(Lead.country != '').group_by(Lead.country).order_by(
        func.count(Lead.id).desc()
    ).limit(10).all()

    # Daily sent (last 7 days)
    daily_sent = []
    for i in range(6, -1, -1):
        day = datetime.utcnow() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59)
        count = Lead.query.filter(
            Lead.email_status == 'sent',
            Lead.last_contacted >= day_start,
            Lead.last_contacted <= day_end
        ).count()
        daily_sent.append({'date': day.strftime('%b %d'), 'count': count})

    # Recent campaigns
    campaigns = Campaign.query.order_by(Campaign.created_at.desc()).limit(10).all()

    return jsonify({
        'total': total,
        'contacted': contacted,
        'sent': sent,
        'failed': failed,
        'success_rate': success_rate,
        'countries': [{'country': c[0], 'count': c[1]} for c in country_counts],
        'daily_sent': daily_sent,
        'campaigns': [c.to_dict() for c in campaigns]
    })


# ─── Routes: Settings ─────────────────────────────────────────────────────────

@app.route('/settings')
def settings_page():
    settings_data = {
        'mail_server': Settings.get('mail_server', 'smtp.gmail.com'),
        'mail_port': Settings.get('mail_port', '587'),
        'mail_use_tls': Settings.get('mail_use_tls', 'true'),
        'mail_username': Settings.get('mail_username', ''),
        'mail_password': Settings.get('mail_password', ''),
        'serpapi_key': Settings.get('serpapi_key', ''),
        'google_delay': Settings.get('google_delay', '2'),
        'max_pages': Settings.get('max_pages', '5'),
        'whatsapp_number': Settings.get('whatsapp_number', '+977-9800000000'),
        'product_catalog_pdf': Settings.get('product_catalog_pdf', ''),
        'unsubscribe_url': Settings.get('unsubscribe_url', ''),
    }
    return render_template('settings.html', active_page='settings', settings=settings_data)


@app.route('/api/settings/smtp', methods=['POST'])
def api_save_smtp():
    data = request.get_json()
    fields = ['mail_server', 'mail_port', 'mail_use_tls', 'mail_username', 'mail_password']
    for field in fields:
        if field in data:
            Settings.set(field, str(data[field]))
    return jsonify({'message': 'SMTP settings saved'})


@app.route('/api/settings/search', methods=['POST'])
def api_save_search_settings():
    data = request.get_json()
    fields = ['serpapi_key', 'google_delay', 'max_pages', 'whatsapp_number', 'product_catalog_pdf', 'unsubscribe_url']
    for field in fields:
        if field in data:
            Settings.set(field, str(data[field]))
    return jsonify({'message': 'Search settings saved'})


@app.route('/api/settings/test-smtp', methods=['POST'])
def api_test_smtp():
    smtp_config = {
        'mail_server': Settings.get('mail_server', 'smtp.gmail.com'),
        'mail_port': Settings.get('mail_port', '587'),
        'mail_use_tls': Settings.get('mail_use_tls', 'true'),
        'mail_username': Settings.get('mail_username', ''),
        'mail_password': Settings.get('mail_password', ''),
    }
    result = test_smtp_connection(smtp_config)
    return jsonify(result)


# ─── Routes: Export ──────────────────────────────────────────────────────────

@app.route('/api/export/csv')
def export_csv():
    leads = Lead.query.order_by(Lead.created_at.desc()).all()
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['ID', 'Business Name', 'Owner Name', 'Email', 'Phone',
                     'Country', 'Website', 'Source URL', 'Score', 'Contacted',
                     'Email Status', 'Created At', 'Last Contacted'])
    for lead in leads:
        writer.writerow([
            lead.id, lead.business_name, lead.owner_name, lead.email,
            lead.phone, lead.country, lead.website, lead.source_url,
            lead.score, 'Yes' if lead.contacted else 'No', lead.email_status,
            lead.created_at.strftime('%Y-%m-%d %H:%M') if lead.created_at else '',
            lead.last_contacted.strftime('%Y-%m-%d %H:%M') if lead.last_contacted else ''
        ])
    output = si.getvalue()
    return Response(
        output,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=singing_bowl_leads_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
    )


@app.route('/api/export/excel')
def export_excel():
    leads = Lead.query.order_by(Lead.created_at.desc()).all()
    data = []
    for lead in leads:
        data.append({
            'ID': lead.id,
            'Business Name': lead.business_name or '',
            'Owner Name': lead.owner_name or '',
            'Email': lead.email,
            'Phone': lead.phone or '',
            'Country': lead.country or '',
            'Website': lead.website or '',
            'Source URL': lead.source_url or '',
            'Score': lead.score,
            'Contacted': 'Yes' if lead.contacted else 'No',
            'Email Status': lead.email_status or '',
            'Created At': lead.created_at.strftime('%Y-%m-%d %H:%M') if lead.created_at else '',
            'Last Contacted': lead.last_contacted.strftime('%Y-%m-%d %H:%M') if lead.last_contacted else ''
        })

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Leads', index=False)
        # Auto-fit columns
        ws = writer.sheets['Leads']
        for column in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in column)
            ws.column_dimensions[column[0].column_letter].width = min(max_len + 4, 50)

    output.seek(0)
    filename = f'singing_bowl_leads_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


# ─── Routes: Database Reset ───────────────────────────────────────────────────

@app.route('/api/reset-database', methods=['POST'])
def api_reset_database():
    try:
        Lead.query.delete()
        Campaign.query.delete()
        db.session.commit()
        logger.warning("Database reset performed - all leads and campaigns deleted")
        return jsonify({'message': 'Database has been reset. All leads and campaigns deleted.'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database reset error: {e}")
        return jsonify({'error': str(e)}), 500


# ─── Routes: Campaigns ───────────────────────────────────────────────────────

@app.route('/campaigns')
def campaigns_page():
    campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
    return render_template('campaigns.html', active_page='campaigns', campaigns=campaigns)


# ─── Error Handlers ──────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


# ─── Run ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
