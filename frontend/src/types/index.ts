export type UserRole = 'SUPER_ADMIN' | 'AGENCY_ADMIN' | 'STAFF';

// -----------------------------------------------------------------------
// Document Category Slugs
// Matches the CATEGORY_CHOICES on the backend Document model
// -----------------------------------------------------------------------
export type DocumentCategory =
  | 'passport'
  | 'bank_statement'
  | 'salary_slip'
  | 'employment_letter'
  | 'tax_return'
  | 'travel_history'
  | 'invitation_letter'
  | 'hotel_booking'
  | 'flight_booking'
  | 'cover_letter'
  | 'other';

export const DOCUMENT_CATEGORY_LABELS: Record<DocumentCategory, string> = {
  passport: 'Passport',
  bank_statement: 'Bank Statement',
  salary_slip: 'Salary Slip',
  employment_letter: 'Employment Letter',
  tax_return: 'Tax Return / ITR',
  travel_history: 'Travel History',
  invitation_letter: 'Invitation Letter',
  hotel_booking: 'Hotel Booking',
  flight_booking: 'Flight Booking',
  cover_letter: 'Cover Letter',
  other: 'Other Document',
};

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';
export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed';

// -----------------------------------------------------------------------
// Core Data Models
// -----------------------------------------------------------------------

export interface Organization {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  organization: string | null;
  organization_name: string | null;
  is_active: boolean;
  date_joined: string;
}

export interface Client {
  id: string;
  organization: string;
  name: string;
  passport_number: string;
  country: string;
  visa_type: string;
  mobile: string;
  email: string;
  notes: string | null;
  created_date: string;
  status: 'Draft' | 'Pending' | 'Under Review' | 'Approved' | 'Rejected';
}

// -----------------------------------------------------------------------
// Risk Factor — detected by the risk assessment engine
// -----------------------------------------------------------------------
export interface RiskFactor {
  factor: string;
  severity: RiskLevel;
  detail: string;
  category: string;
}

// -----------------------------------------------------------------------
// Eligibility Score Category Breakdown
// -----------------------------------------------------------------------
export interface EligibilityScoreBreakdown {
  score: number;
  weight: number;
  contribution: number;
  detail: string;
}

// -----------------------------------------------------------------------
// AI Eligibility Score — 5-category weighted assessment
// -----------------------------------------------------------------------
export interface EligibilityScore {
  id: string;
  submission: string;
  financial_score: number;
  employment_score: number;
  travel_history_score: number;
  documentation_score: number;
  compliance_score: number;
  final_score: number;
  weighted_breakdown: {
    financial: EligibilityScoreBreakdown;
    employment: EligibilityScoreBreakdown;
    travel_history: EligibilityScoreBreakdown;
    documentation: EligibilityScoreBreakdown;
    compliance: EligibilityScoreBreakdown;
  };
  risk_level: RiskLevel;
  risk_factors: RiskFactor[];
  cross_validation_results: CrossValidationResults;
  recommendations: string[];
  strengths: string[];
  is_eligible: boolean;
  eligibility_summary: string;
  created_at: string;
  updated_at: string;
}

// -----------------------------------------------------------------------
// Cross-Document Validation Results
// -----------------------------------------------------------------------
export interface CrossValidationCheck {
  check: string;
  result: 'PASS' | 'FAIL' | 'WARNING';
  severity: RiskLevel;
  detail: string;
  data: Record<string, any>;
}

export interface CrossValidationResults {
  checks: CrossValidationCheck[];
  passed: number;
  failed: number;
  warnings: number;
  overall_status: 'PASS' | 'WARNING' | 'FAIL';
  risk_level: RiskLevel;
  consistency_score: number;
}

// -----------------------------------------------------------------------
// Document — enhanced with AI fields
// -----------------------------------------------------------------------
export interface Document {
  id: string;
  submission: string;
  name: string;
  category: DocumentCategory;
  file_url: string;
  status: 'Pending' | 'Valid' | 'Invalid';
  file_size: number | null;
  file_type: string | null;
  confidence_score: number;
  extracted_data: Record<string, any>;
  ai_analysis: Record<string, any>;
  validation_result: Record<string, any>;
  created_at: string;
}

// -----------------------------------------------------------------------
// Processing Log Entry
// -----------------------------------------------------------------------
export interface ProcessingLogEntry {
  timestamp: string;
  event: string;
  details: Record<string, any>;
}

// -----------------------------------------------------------------------
// Validation Report (rules engine)
// -----------------------------------------------------------------------
export interface ValidationReport {
  id: string;
  submission: string;
  score: number;
  status: 'Passed' | 'Warning' | 'Failed';
  correct_documents: string[];
  missing_documents: string[];
  issues: string[];
  recommendations: string | null;
  created_at: string;
}

// -----------------------------------------------------------------------
// Submission — enhanced with AI pipeline fields
// -----------------------------------------------------------------------
export interface Submission {
  id: string;
  application_id: string;
  client: string;
  client_detail: Client;
  country: string;
  visa_type: string;
  status: 'Draft' | 'Pending' | 'Under Review' | 'Approved' | 'Rejected';
  processing_status: ProcessingStatus;
  processing_logs: ProcessingLogEntry[];
  created_by: string | null;
  created_by_email: string | null;
  created_at: string;
  updated_at: string;
  documents: Document[];
  validation_report: ValidationReport | null;
  eligibility_score: EligibilityScore | null;
}

export interface CountryRule {
  id: string;
  country: string;
  visa_type: string;
  required_documents: string[];
  rules: {
    passport_min_validity_months?: number;
    min_bank_balance?: number;
    min_employment_months?: number;
    required_travel_history?: boolean;
    income_multiplier?: number;
    [key: string]: any;
  };
  created_at: string;
  updated_at: string;
}

export interface ActivityLog {
  id: string;
  user: string | null;
  user_email: string | null;
  organization: string;
  action: string;
  details: Record<string, any>;
  timestamp: string;
}

// -----------------------------------------------------------------------
// Dashboard Data — enhanced with AI metrics
// -----------------------------------------------------------------------
export interface DashboardTrends {
  month: string;
  submissions: number;
  approved: number;
  rejected: number;
}

export interface DashboardCountry {
  country: string;
  value: number;
}

export interface DashboardScoreDistribution {
  range: string;
  count: number;
}

export interface DashboardMetrics {
  total_clients: number;
  total_submissions: number;
  approved: number;
  rejected: number;
  pending: number;
  under_review: number;
  approval_rate: number;
  avg_score: number;
  // New AI metrics
  total_ai_assessed: number;
  avg_eligibility_score: number;
  risk_distribution: {
    LOW: number;
    MEDIUM: number;
    HIGH: number;
  };
}

export interface DashboardData {
  metrics: DashboardMetrics;
  trends: DashboardTrends[];
  countries: DashboardCountry[];
  score_distribution: DashboardScoreDistribution[];
  recent_activity: ActivityLog[];
}
