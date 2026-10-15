"""French/English A4 documents generated from immutable invoice snapshots."""
import io
import base64
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from localization import language as validate_language

LABELS = {
    'fr': {
        'invoice': 'FACTURE', 'date': 'Date', 'customer': 'Client',
        'cancelled': 'VENTE ANNULÉE — DOCUMENT HISTORIQUE',
        'description': 'Désignation', 'quantity': 'Qté',
        'unit': 'Prix unitaire HT', 'line_total': 'Total HT',
        'subtotal': 'Sous-total HT', 'discount': 'Remise', 'tax': 'TVA',
        'total': 'Total TTC', 'paid': 'Montant payé', 'due': 'Restant dû',
        'note': 'Document de gestion. Numérotation et mentions réglementaires à valider avant émission commerciale.',
        'page': 'Page',
    },
    'en': {
        'invoice': 'INVOICE', 'date': 'Date', 'customer': 'Customer',
        'cancelled': 'CANCELLED SALE — HISTORICAL DOCUMENT',
        'description': 'Description', 'quantity': 'Qty',
        'unit': 'Unit price excl. VAT', 'line_total': 'Total excl. VAT',
        'subtotal': 'Subtotal excl. VAT', 'discount': 'Discount', 'tax': 'VAT',
        'total': 'Total incl. VAT', 'paid': 'Amount paid', 'due': 'Balance due',
        'note': 'Management document. Numbering and statutory disclosures must be approved before commercial use.',
        'page': 'Page',
    },
}

def pdf(invoice, language='fr'):
    labels = LABELS[validate_language(language)]
    out = io.BytesIO()
    styles = getSampleStyleSheet()
    green = colors.HexColor('#176b52')
    company, sale, shop = invoice['company'], invoice['sale'], invoice['shop']
    number = 'F-' + str(sale['id']).zfill(6)
    document = SimpleDocTemplate(out, pagesize=A4, rightMargin=42, leftMargin=42,
                                topMargin=40, bottomMargin=40,
                                title=labels['invoice']+' '+number, author=company['name'])
    story = []

    def text(value, style='Normal'):
        return Paragraph(escape(str(value)), styles[style])

    def amount(cents):
        value = f'{cents/100:,.2f}'
        if language == 'fr':
            value = value.replace(',', ' ').replace('.', ',')
        return value + ' MAD'

    if company.get('logo'):
        raw = base64.b64decode(company['logo'].split(',')[1])
        image = Image(io.BytesIO(raw))
        image._restrictSize(110, 65)
        story.extend([image, Spacer(1, 12)])
    story.extend([
        text(company['name'], 'Title'), text(shop['name']),
        text(company.get('address') or shop['address']),
        text('ICE : '+company.get('ice', '')+' • IF : '+company.get('tax_id', '')),
        Spacer(1, 28), text(labels['invoice']+' '+number, 'Heading1'),
        text(labels['date']+' : '+sale['date'][:10]),
        text(labels['customer']+' : '+sale['client']), Spacer(1, 20),
    ])
    if sale['status'] == 'Annulée':
        story.extend([text(labels['cancelled'], 'Heading2'), Spacer(1, 10)])
    data = [[text(labels[key]) for key in ['description', 'quantity', 'unit', 'line_total']]]
    for line in invoice['lines']:
        data.append([text(line['name']), text(line['quantity']),
                     text(amount(line['price'])), text(amount(line['quantity']*line['price']))])
    table = Table(data, colWidths=[235, 35, 110, 105], repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#edf5ee')),
        ('LINEBELOW', (0, 0), (-1, 0), 1, green),
        ('LINEBELOW', (0, 1), (-1, -1), .4, colors.HexColor('#e0e6df')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.extend([table, Spacer(1, 25)])
    for key in ['subtotal', 'discount', 'tax', 'total', 'paid']:
        story.append(text(labels[key]+' : '+amount(sale[key]), 'Heading3' if key == 'total' else 'Normal'))
    story.extend([text(labels['due']+' : '+amount(sale['total']-sale['paid'])),
                  Spacer(1, 35), text(labels['note'])])

    def footer(canvas, doc):
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.gray)
        canvas.drawString(42, 25, 'Bazar • '+company['name'][:60])
        canvas.drawRightString(A4[0]-42, 25, labels['page']+' '+str(doc.page))

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return out.getvalue()
