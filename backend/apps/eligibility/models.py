import uuid
from django.db import models


class EligibilityScore(models.Model):
    """
    Stores the AI-computed eligibility assessment for a visa submission.
    Breaks down into 5 weighted categories that produce a final eligibility score.

    Scoring Categories:
        - financial_score     (weight 30%): bank balance, income, financial stability
        - employment_score    (weight 25%): employment letter, salary slip consistency
        - travel_history_score(weight 15%): countries visited, visa history, frequency
        - documentation_score (weight 15%): OCR confidence, document completeness
        - compliance_score    (weight 15%): country-specific rule pass rate

    Final score = weighted average of all 5 categories (0–100).
    Risk level is derived from missing docs, inconsistencies, and rule failures.
    """

    RISK_LEVEL_CHOICES = [
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # OneToOne link to the Submission — one eligibility assessment per application
    submission = models.OneToOneField(
        'submissions.Submission',
        on_delete=models.CASCADE,
        related_name='eligibility_score'
    )

    # --- Individual Category Scores (0–100 each) ---
    financial_score = models.IntegerField(
        default=0,
        help_text="Financial strength score based on bank balance and income (0–100)"
    )
    employment_score = models.IntegerField(
        default=0,
        help_text="Employment stability score based on letter and salary slip (0–100)"
    )
    travel_history_score = models.IntegerField(
        default=0,
        help_text="Travel history score based on countries visited and visa history (0–100)"
    )
    documentation_score = models.IntegerField(
        default=0,
        help_text="Documentation quality score based on OCR confidence and completeness (0–100)"
    )
    compliance_score = models.IntegerField(
        default=0,
        help_text="Country rule compliance score — pass rate of all country-specific rules (0–100)"
    )

    # --- Final Weighted Score ---
    final_score = models.IntegerField(
        default=0,
        help_text="Weighted final eligibility score (0–100). Threshold: 70+ = Eligible"
    )

    # Breakdown detail: {"financial": {"score": 92, "weight": 0.30, "contribution": 27.6, ...}, ...}
    weighted_breakdown = models.JSONField(
        default=dict, blank=True,
        help_text="Per-category score breakdown with weights and contributions"
    )

    # --- Risk Assessment ---
    risk_level = models.CharField(
        max_length=10, choices=RISK_LEVEL_CHOICES, default='HIGH',
        help_text="Overall application risk level: LOW, MEDIUM, or HIGH"
    )

    # List of identified risk factors: [{"factor": "...", "severity": "HIGH", "detail": "..."}]
    risk_factors = models.JSONField(
        default=list, blank=True,
        help_text="List of identified risk factors with severity levels"
    )

    # --- Cross-Document Validation ---
    # Results from consistency checks across all uploaded documents
    cross_validation_results = models.JSONField(
        default=dict, blank=True,
        help_text="Cross-document consistency check results"
    )

    # --- AI Recommendations ---
    # Actionable steps to improve eligibility: ["Increase bank balance by ₹X", ...]
    recommendations = models.JSONField(
        default=list, blank=True,
        help_text="Ordered list of AI-generated actionable recommendations"
    )

    # --- Strengths ---
    strengths = models.JSONField(
        default=list, blank=True,
        help_text="List of application strengths identified by the AI engine"
    )

    # --- Eligibility Determination ---
    # Overall AI determination (separate from rules engine status)
    is_eligible = models.BooleanField(
        default=False,
        help_text="AI-determined eligibility (final_score >= 70 and no HIGH risk factors)"
    )
    eligibility_summary = models.TextField(
        blank=True, default='',
        help_text="Human-readable AI eligibility summary paragraph"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Eligibility Score'
        verbose_name_plural = 'Eligibility Scores'
        ordering = ['-created_at']

    def __str__(self):
        return f"EligibilityScore for {self.submission.application_id} — {self.final_score}/100 ({self.risk_level})"
