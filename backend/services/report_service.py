"""
Enhanced Report Generation Service
=====================================
Generates professional PDF reports using ReportLab.
Includes both the rules-engine compliance results AND the AI eligibility assessment.

Report Sections:
    1. Header (VisaFlow AI branding)
    2. Applicant Information
    3. Uploaded Documents Summary
    4. Rules Engine Compliance Score
    5. AI Eligibility Score Breakdown (5 categories)
    6. Risk Assessment
    7. Cross-Document Validation
    8. Strengths
    9. Issues & Warnings
    10. AI Recommendations
    11. Final Assessment Verdict
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from django.conf import settings


def generate_report_pdf(report, output_path: str, eligibility_score=None) -> str:
    """
    Generate the enhanced PDF report combining rules engine + AI assessment.

    Args:
        report: ValidationReport model instance
        output_path: Absolute path to write the PDF
        eligibility_score: Optional EligibilityScore model instance

    Returns:
        str: Path to the generated PDF
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50,
    )

    story = []
    styles = _build_styles()

    # -----------------------------------------------------------------------
    # 1. HEADER
    # -----------------------------------------------------------------------
    story.append(Paragraph("VisaFlow AI — Visa Eligibility Assessment Report", styles['title']))
    generated_at = report.created_at.strftime('%B %d, %Y at %H:%M UTC')
    story.append(Paragraph(f"Generated: {generated_at}", styles['muted']))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#334155')))
    story.append(Spacer(1, 12))

    # -----------------------------------------------------------------------
    # 2. APPLICANT INFORMATION
    # -----------------------------------------------------------------------
    submission = report.submission
    client = submission.client

    story.append(Paragraph("Applicant Information", styles['section']))
    applicant_data = [
        [_bold("Applicant Name:", styles), _cell(client.name, styles),
         _bold("Application ID:", styles), _cell(submission.application_id, styles)],
        [_bold("Passport Number:", styles), _cell(client.passport_number, styles),
         _bold("Destination:", styles), _cell(f"{submission.country}", styles)],
        [_bold("Visa Type:", styles), _cell(submission.visa_type, styles),
         _bold("Application Status:", styles), _cell(submission.status, styles)],
        [_bold("Contact Email:", styles), _cell(client.email, styles),
         _bold("Mobile:", styles), _cell(client.mobile, styles)],
    ]
    story.append(_info_table(applicant_data))
    story.append(Spacer(1, 15))

    # -----------------------------------------------------------------------
    # 3. RULES ENGINE COMPLIANCE SCORE
    # -----------------------------------------------------------------------
    story.append(Paragraph("Rules Engine Compliance", styles['section']))

    score_color = '#10b981'
    if report.status == 'Warning':
        score_color = '#f59e0b'
    elif report.status == 'Failed':
        score_color = '#ef4444'

    score_data = [[
        Paragraph(f"<font size=13><b>Compliance Score</b></font>", styles['body']),
        Paragraph(f"<font size=32 color='{score_color}'><b>{report.score}/100</b></font>", styles['body']),
        Paragraph(f"<font size=13><b>Status: {report.status}</b></font>", styles['body']),
    ]]
    score_table = Table(score_data, colWidths=[2.2 * inch, 2.5 * inch, 2.3 * inch])
    score_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 15))

    # -----------------------------------------------------------------------
    # 4. AI ELIGIBILITY SCORE BREAKDOWN (if available)
    # -----------------------------------------------------------------------
    if eligibility_score:
        story.append(Paragraph("AI Eligibility Assessment", styles['section']))

        # Final score banner
        final_color = '#10b981' if eligibility_score.is_eligible else '#ef4444'
        verdict = "ELIGIBLE ✓" if eligibility_score.is_eligible else "NOT ELIGIBLE ✗"
        risk_bg = {
            'LOW': '#dcfce7', 'MEDIUM': '#fef9c3', 'HIGH': '#fee2e2'
        }.get(eligibility_score.risk_level, '#f1f5f9')
        risk_color = {
            'LOW': '#166534', 'MEDIUM': '#854d0e', 'HIGH': '#991b1b'
        }.get(eligibility_score.risk_level, '#334155')

        ai_banner_data = [[
            Paragraph(f"<font size=28 color='{final_color}'><b>{eligibility_score.final_score}/100</b></font>", styles['body']),
            Paragraph(f"<font size=14 color='{final_color}'><b>{verdict}</b></font><br/><font size=9 color='#64748b'>AI Eligibility Score</font>", styles['body']),
            Paragraph(f"<font size=12><b>Risk Level</b></font><br/><font size=14 color='{risk_color}'><b>{eligibility_score.risk_level}</b></font>", styles['body']),
        ]]
        ai_banner = Table(ai_banner_data, colWidths=[2.0 * inch, 3.0 * inch, 2.0 * inch])
        ai_banner.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#f8fafc')),
            ('BACKGROUND', (2, 0), (2, 0), colors.HexColor(risk_bg)),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor(final_color)),
            ('LINEAFTER', (1, 0), (1, 0), 1, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(ai_banner)
        story.append(Spacer(1, 10))

        # 5-Category Score Breakdown
        story.append(Paragraph("Score Breakdown by Category", styles['subsection']))
        breakdown = eligibility_score.weighted_breakdown or {}
        cat_labels = {
            'financial': ('Financial Strength', '30%'),
            'employment': ('Employment Stability', '25%'),
            'travel_history': ('Travel History', '15%'),
            'documentation': ('Documentation Quality', '15%'),
            'compliance': ('Rule Compliance', '15%'),
        }
        scores_data = [
            [
                Paragraph("<b>Category</b>", styles['small_bold']),
                Paragraph("<b>Weight</b>", styles['small_bold']),
                Paragraph("<b>Score</b>", styles['small_bold']),
                Paragraph("<b>Contribution</b>", styles['small_bold']),
                Paragraph("<b>Detail</b>", styles['small_bold']),
            ]
        ]
        category_scores = [
            ('financial', eligibility_score.financial_score),
            ('employment', eligibility_score.employment_score),
            ('travel_history', eligibility_score.travel_history_score),
            ('documentation', eligibility_score.documentation_score),
            ('compliance', eligibility_score.compliance_score),
        ]
        for cat_key, cat_score in category_scores:
            label, weight = cat_labels.get(cat_key, (cat_key, '?'))
            cat_data = breakdown.get(cat_key, {})
            contribution = cat_data.get('contribution', 0)
            detail = str(cat_data.get('detail', ''))[:80]
            score_col = f"<font color='{'#10b981' if cat_score >= 70 else '#f59e0b' if cat_score >= 50 else '#ef4444'}'><b>{cat_score}</b></font>"
            scores_data.append([
                Paragraph(label, styles['small']),
                Paragraph(weight, styles['small']),
                Paragraph(score_col, styles['small']),
                Paragraph(f"{contribution:.1f}", styles['small']),
                Paragraph(detail, styles['tiny']),
            ])

        cat_table = Table(scores_data, colWidths=[1.6 * inch, 0.7 * inch, 0.6 * inch, 0.9 * inch, 3.2 * inch])
        cat_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (3, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(cat_table)
        story.append(Spacer(1, 15))

        # Eligibility Summary
        if eligibility_score.eligibility_summary:
            story.append(Paragraph("AI Assessment Summary", styles['subsection']))
            summary_box = Table(
                [[Paragraph(eligibility_score.eligibility_summary, styles['recommendation'])]],
                colWidths=[7.0 * inch]
            )
            summary_box.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eff6ff')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#bfdbfe')),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ]))
            story.append(summary_box)
            story.append(Spacer(1, 15))

    # -----------------------------------------------------------------------
    # 5. DOCUMENT VERIFICATION STATUS
    # -----------------------------------------------------------------------
    story.append(Paragraph("Document Verification Status", styles['section']))
    doc_header = [
        _bold("Document Type", styles), _bold("Category", styles),
        _bold("Status", styles), _bold("OCR Confidence", styles), _bold("Findings", styles)
    ]
    doc_rows = [doc_header]

    for doc in submission.documents.all():
        status_color = '#10b981' if doc.status == 'Valid' else '#ef4444'
        confidence = f"{doc.confidence_score:.0%}" if doc.confidence_score else "N/A"
        detail = str(doc.validation_result.get('details', doc.validation_result.get('errors', 'Checked')))[:60]
        doc_rows.append([
            Paragraph(doc.name, styles['small']),
            Paragraph(doc.category.replace('_', ' ').title(), styles['small']),
            Paragraph(f"<font color='{status_color}'><b>{doc.status}</b></font>", styles['small']),
            Paragraph(confidence, styles['small']),
            Paragraph(detail, styles['tiny']),
        ])

    for missing in report.missing_documents:
        doc_rows.append([
            Paragraph(missing, styles['small']),
            Paragraph("—", styles['small']),
            Paragraph("<font color='#ef4444'><b>Missing</b></font>", styles['small']),
            Paragraph("—", styles['small']),
            Paragraph("Required document not uploaded", styles['tiny']),
        ])

    doc_table = Table(doc_rows, colWidths=[1.4 * inch, 1.2 * inch, 0.8 * inch, 0.9 * inch, 2.7 * inch])
    doc_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(doc_table)
    story.append(Spacer(1, 15))

    # -----------------------------------------------------------------------
    # 6. RISK FACTORS (if AI assessment available)
    # -----------------------------------------------------------------------
    if eligibility_score and eligibility_score.risk_factors:
        story.append(Paragraph("Risk Assessment", styles['section']))
        risk_colors = {'HIGH': '#ef4444', 'MEDIUM': '#f59e0b', 'LOW': '#10b981'}
        for risk in eligibility_score.risk_factors:
            sev = risk.get('severity', 'LOW')
            color = risk_colors.get(sev, '#64748b')
            story.append(Paragraph(
                f"<font color='{color}'><b>[{sev}]</b></font> <b>{risk.get('factor', '')}</b> — {risk.get('detail', '')}",
                styles['body']
            ))
        story.append(Spacer(1, 10))

    # -----------------------------------------------------------------------
    # 7. STRENGTHS (if AI assessment available)
    # -----------------------------------------------------------------------
    if eligibility_score and eligibility_score.strengths:
        story.append(Paragraph("Application Strengths", styles['section']))
        for strength in eligibility_score.strengths:
            story.append(Paragraph(f"<font color='#10b981'>✓</font> {strength}", styles['body']))
        story.append(Spacer(1, 10))

    # -----------------------------------------------------------------------
    # 8. ISSUES & WARNINGS
    # -----------------------------------------------------------------------
    if report.issues:
        story.append(Paragraph("Identified Issues & Warnings", styles['section']))
        for issue in report.issues:
            story.append(Paragraph(f"<font color='#ef4444'>•</font> {issue}", styles['body']))
        story.append(Spacer(1, 10))

    # -----------------------------------------------------------------------
    # 9. RECOMMENDATIONS
    # -----------------------------------------------------------------------
    story.append(Paragraph("Recommendations", styles['section']))

    # Use AI recommendations if available, else rules engine recommendations
    if eligibility_score and eligibility_score.recommendations:
        for i, rec in enumerate(eligibility_score.recommendations, 1):
            story.append(Paragraph(f"{i}. {rec}", styles['recommendation']))
    elif report.recommendations:
        recommendation_box = Table(
            [[Paragraph(report.recommendations, styles['recommendation'])]],
            colWidths=[7.0 * inch]
        )
        recommendation_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eff6ff')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#bfdbfe')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(recommendation_box)

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1')))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "This report is generated by VisaFlow AI and is for advisory purposes only. "
        "Final visa decisions rest with the respective embassy or consulate.",
        styles['tiny']
    ))

    doc.build(story)
    return output_path


# ---------------------------------------------------------------------------
# Style Helpers
# ---------------------------------------------------------------------------

def _build_styles() -> dict:
    base = getSampleStyleSheet()
    return {
        'title': ParagraphStyle('Title', parent=base['Heading1'],
                                fontName='Helvetica-Bold', fontSize=20, leading=24,
                                textColor=colors.HexColor('#0f172a'), spaceAfter=6),
        'section': ParagraphStyle('Section', parent=base['Heading2'],
                                  fontName='Helvetica-Bold', fontSize=13, leading=16,
                                  textColor=colors.HexColor('#1e293b'), spaceBefore=12, spaceAfter=6),
        'subsection': ParagraphStyle('Sub', parent=base['Heading3'],
                                     fontName='Helvetica-Bold', fontSize=11,
                                     textColor=colors.HexColor('#334155'), spaceBefore=8, spaceAfter=4),
        'body': ParagraphStyle('Body', parent=base['Normal'],
                               fontName='Helvetica', fontSize=10, leading=14,
                               textColor=colors.HexColor('#334155'), spaceAfter=4),
        'bold': ParagraphStyle('Bold', parent=base['Normal'],
                               fontName='Helvetica-Bold', fontSize=10,
                               textColor=colors.HexColor('#1e293b')),
        'small': ParagraphStyle('Small', parent=base['Normal'],
                                fontName='Helvetica', fontSize=9, leading=12,
                                textColor=colors.HexColor('#334155')),
        'small_bold': ParagraphStyle('SmallBold', parent=base['Normal'],
                                     fontName='Helvetica-Bold', fontSize=9,
                                     textColor=colors.HexColor('#1e293b')),
        'tiny': ParagraphStyle('Tiny', parent=base['Normal'],
                               fontName='Helvetica', fontSize=8, leading=10,
                               textColor=colors.HexColor('#64748b')),
        'muted': ParagraphStyle('Muted', parent=base['Normal'],
                                fontName='Helvetica', fontSize=9,
                                textColor=colors.HexColor('#64748b'), spaceAfter=4),
        'recommendation': ParagraphStyle('Rec', parent=base['Normal'],
                                         fontName='Helvetica-Oblique', fontSize=10, leading=15,
                                         textColor=colors.HexColor('#1e3a8a')),
    }


def _bold(text: str, styles: dict) -> Paragraph:
    return Paragraph(f"<b>{text}</b>", styles['small'])


def _cell(text: str, styles: dict) -> Paragraph:
    return Paragraph(str(text), styles['small'])


def _info_table(data: list) -> Table:
    table = Table(data, colWidths=[1.5 * inch, 2.0 * inch, 1.5 * inch, 2.0 * inch])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f8fafc')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    return table
