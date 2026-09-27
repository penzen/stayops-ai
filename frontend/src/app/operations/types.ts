export type CaseData = {
  case_id: string;
  booking_id: string;
  property_id: string;
  category: string;
  status: string;
  summary: string | null;
  assigned_to: string | null;
  claimed_at: string | null;
  created_at: string;
};

export type Technician = {
  team_id: string;
  team_group: string;
  team_role?: string;
  first_name?: string;
  last_name?: string;
  sector?: string;
};

export type Guest = {
  guest_id: string;
  first_name: string;
  last_name: string;
  guest_lang?: string;
};

export type Booking = {
  booking_id: string;
  guest_id: string;
  property_id: string;
  check_in?: string;
  check_out?: string;
  nights?: number;
  total_price?: number;
};

export type Property = {
  property_id: string;
  title?: string;
  prop_address?: string;
  city?: string;
};

export type Task = {
  task_id: string;
  category: string;
  title: string;
  task_status: string;
  assigned_to?: string | null;
};

export type Escalation = {
  escalation_id: string;
  category: string;
  reason: string;
  priority: string;
  status: string;
  assigned_to?: string | null;
};

export type Operator = {
  team_id: string;
  first_name?: string;
  last_name?: string;
  team_role?: string;
};

export type Handoff = {
  reason: string | null;
  priority: string | null;
  assigned_to: string | null;
  claimed_at: string | null;
};

export type CompensationRequest = {
  compensation_request_id: string;
  case_id: string;
  related_case_id: string | null;
  booking_id: string;
  property_id: string;
  reason: string;
  requested_outcome: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type CompensationDecision = {
  compensation_decision_id: string;
  compensation_request_id: string;
  decision: string;
  amount: number | null;
  currency: string | null;
  reason: string;
  decided_by: string;
  created_at: string;
};

export type CompensationEvidence = {
  compensation_request: CompensationRequest;
  refund_case: CaseData | null;
  related_case: CaseData | null;
  booking: Booking | null;
  property: Property | null;

  operational_evidence: {
    task_count: number;
    escalation_count: number;
    open_task_count: number;
    open_escalation_count: number;
    tasks: Task[];
    escalations: Escalation[];
  };

  decision: CompensationDecision | null;
};

export type QueueEntry = {
  case: CaseData;
  booking: Booking | null;
  guest: Guest | null;
  property: Property | null;
  tasks: Task[];
  escalations: Escalation[];
  operator: Operator | null;
  handoff: Handoff;
  compensation_request:
    CompensationRequest | null;
  compensation_decision:
    CompensationDecision | null;
};

export type CaseEvent = {
  case_event_id: string;
  case_id: string;
  event_type: string;
  actor_type: string;
  actor_id: string | null;
  summary: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type ConversationMessage = {
  message_id: string;
  booking_id: string;
  guest_id: string;
  sender_type: string;
  message_text: string;
  channel: string;
  created_at: string;
};