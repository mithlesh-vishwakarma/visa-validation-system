export type UserRole = 'SUPER_ADMIN' | 'AGENCY_ADMIN' | 'STAFF';

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

export interface Document {
  id: string;
  submission: string;
  name: string;
  file_url: string;
  status: 'Pending' | 'Valid' | 'Invalid';
  file_size: number | null;
  file_type: string | null;
  extracted_data: Record<string, any>;
  validation_result: Record<string, any>;
  created_at: string;
}

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

export interface CountryRule {
  id: string;
  country: string;
  visa_type: string;
  required_documents: string[];
  rules: {
    passport_min_validity_months?: number;
    min_bank_balance?: number;
    [key: string]: any;
  };
  created_at: string;
  updated_at: string;
}

export interface Submission {
  id: string;
  client: string;
  client_detail: Client;
  country: string;
  visa_type: string;
  status: 'Draft' | 'Pending' | 'Under Review' | 'Approved' | 'Rejected';
  created_by: string | null;
  created_by_email: string | null;
  created_at: string;
  updated_at: string;
  documents: Document[];
  validation_report: ValidationReport | null;
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
}

export interface DashboardData {
  metrics: DashboardMetrics;
  trends: DashboardTrends[];
  countries: DashboardCountry[];
  score_distribution: DashboardScoreDistribution[];
  recent_activity: ActivityLog[];
}
