export interface Brand {
  id: number;
  division: string;
  brand_category: string;
  is_active: boolean;
}

export interface Task {
  id: number;
  task_description: string;
  assigned_to: string | null;
  deadline: string | null;
  task_category: string | null;
  task_status: string;
  priority: string;
  occurrence_count: number;
  is_resolved: boolean;
}

export interface Insight {
  id: number;
  insight_type: string | null;
  description: string;
  description_ar: string | null;
  severity: string | null;
  anomaly_score: number | null;
}

export interface ReportItem {
  id: number;
  brand: Brand;
  availability_status: string;
  vendor: string | null;
  milestone: string | null;
  milestone_ar: string | null;
  shipment_bis: string | null;
  comments_actions: string | null;
  comments_actions_ar: string | null;
  quantity_text: string | null;
  financial_text: string | null;
  language: string;
  tasks: Task[];
}

export interface PriorityAction {
  id: number;
  person: string;
  action: string;
  action_ar: string | null;
  category: string | null;
  urgency: string | null;
}

export interface ThreadSummary {
  id: number;
  total_anomalies: number;
  overall_health: string | null;
  sales_timeline: string | null;
  priority_matrix: string | null;
  key_highlights: string | null;
}

export interface Report {
  id: number;
  subject: string;
  report_date: string;
  sender: string | null;
  received_at: string;
  processing_status: string;
  risk_score: number;
  risk_category: string | null;
  items: ReportItem[];
  insights: Insight[];
  priority_actions: PriorityAction[];
  thread_summary: ThreadSummary | null;
}

export interface ReportSummary {
  id: number;
  subject: string;
  report_date: string;
  processing_status: string;
  item_count: number;
  task_count: number;
  insight_count: number;
  created_at: string;
}

export interface DashboardSummary {
  total_brands: number;
  brands_with_issues: number;
  open_tasks: number;
  critical_insights: number;
  last_report_date: string | null;
  status_distribution: Record<string, number>;
}

export interface RiskLanguage {
  id: number;
  phrase: string;
  category: string;
  severity_score: number;
  context: string;
}

export interface PaymentTerm {
  id: number;
  payment_method: string | null;
  deposit_pct: number | null;
  balance_pct: number | null;
  expected_date: string | null;
}

export interface Negotiation {
  id: number;
  type: string | null;
  percentage: number | null;
  status: string;
}

export interface LeadTime {
  id: number;
  days: number | null;
  status: string | null;
}
