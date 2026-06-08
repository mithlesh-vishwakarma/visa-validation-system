import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from django.conf import settings

def generate_report_pdf(report, output_path):
    """
    Generates a production-quality PDF report for a ValidationReport using ReportLab.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    story = []
    styles = getSampleStyleSheet()

    # Define custom styles for a premium look
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=12
    )

    section_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=14,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )

    bold_body_style = ParagraphStyle(
        'BoldBody',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    recommendation_style = ParagraphStyle(
        'Recommendation',
        parent=body_style,
        fontName='Helvetica-Oblique',
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor('#1e3a8a')
    )

    # 1. Header Section
    story.append(Paragraph("VisaFlow AI — Document Compliance Report", title_style))
    story.append(Paragraph(f"Generated on: {report.created_at.strftime('%Y-%m-%d %H:%M UTC')}", body_style))
    story.append(Spacer(1, 15))

    # 2. Metadata Table (Client & Visa Details)
    submission = report.submission
    client = submission.client
    meta_data = [
        [Paragraph("Client Name:", bold_body_style), Paragraph(client.name, body_style),
         Paragraph("Passport Number:", bold_body_style), Paragraph(client.passport_number, body_style)],
        [Paragraph("Destination Country:", bold_body_style), Paragraph(submission.country, body_style),
         Paragraph("Visa Type:", bold_body_style), Paragraph(submission.visa_type, body_style)],
        [Paragraph("Application Status:", bold_body_style), Paragraph(submission.status, body_style),
         Paragraph("Submission ID:", bold_body_style), Paragraph(str(submission.id)[:18] + "...", body_style)]
    ]
    
    meta_table = Table(meta_data, colWidths=[1.5*inch, 2.0*inch, 1.5*inch, 2.0*inch])
    meta_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f8fafc')),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#f8fafc')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 20))

    # 3. Compliance Score Block
    score_color = '#10b981' # green
    if report.status == 'Warning':
        score_color = '#f59e0b' # yellow/orange
    elif report.status == 'Failed':
        score_color = '#ef4444' # red

    score_data = [
        [
            Paragraph("<font size=14><b>Compliance Score</b></font>", body_style),
            Paragraph(f"<font size=28 color='{score_color}'><b>{report.score}/100</b></font>", body_style),
            Paragraph(f"<font size=14><b>Status: {report.status}</b></font>", body_style)
        ]
    ]
    score_table = Table(score_data, colWidths=[2.3*inch, 2.4*inch, 2.3*inch])
    score_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 20))

    # 4. Document Audit Status Table
    story.append(Paragraph("Document Verification Status", section_style))
    
    doc_header = [
        Paragraph("<b>Document Type</b>", bold_body_style),
        Paragraph("<b>Status</b>", bold_body_style),
        Paragraph("<b>OCR Verification Details</b>", bold_body_style)
    ]
    doc_rows = [doc_header]

    # Add correct documents
    for doc in submission.documents.all():
        doc_rows.append([
            Paragraph(doc.name, body_style),
            Paragraph(f"<font color='green'><b>{doc.status}</b></font>" if doc.status == 'Valid' else f"<font color='red'><b>{doc.status}</b></font>", body_style),
            Paragraph(str(doc.validation_result.get('details', doc.validation_result.get('errors', 'Checked'))), body_style)
        ])

    # Add missing required documents
    for missing in report.missing_documents:
        doc_rows.append([
            Paragraph(missing, body_style),
            Paragraph("<font color='red'><b>Missing</b></font>", body_style),
            Paragraph("Required document not uploaded", body_style)
        ])

    doc_table = Table(doc_rows, colWidths=[2.0*inch, 1.2*inch, 3.8*inch])
    doc_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e2e8f0')),
    ]))
    story.append(doc_table)
    story.append(Spacer(1, 20))

    # 5. Issues & Warnings list
    if report.issues:
        story.append(Paragraph("Identified Compliance Issues & Warnings", section_style))
        for issue in report.issues:
            story.append(Paragraph(f"<font color='#ef4444'>•</font> {issue}", body_style))
        story.append(Spacer(1, 15))

    # 6. Recommendations Block
    story.append(Paragraph("Consultant Recommendations", section_style))
    recommendation_box = Table([[Paragraph(report.recommendations or "No immediate action required.", recommendation_style)]], colWidths=[7.0*inch])
    recommendation_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#eff6ff')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#bfdbfe')),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(recommendation_box)

    # Build PDF
    doc.build(story)
    return output_path
