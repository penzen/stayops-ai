"use client";

import Link from "next/link";

import {
  useCallback,
  useEffect,
  useState,
} from "react";


type CaseData = {
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


type Guest = {
  guest_id: string;
  first_name: string;
  last_name: string;
  guest_lang?: string;
};


type Booking = {
  booking_id: string;
  guest_id: string;
  property_id: string;
  check_in?: string;
  check_out?: string;
};


type Property = {
  property_id: string;
  title?: string;
};


type Task = {
  task_id: string;
  category: string;
  title: string;
  task_status: string;
  assigned_to?: string | null;
};


type Escalation = {
  escalation_id: string;
  category: string;
  reason: string;
  priority: string;
  status: string;
  assigned_to?: string | null;
};


type Operator = {
  team_id: string;
  first_name?: string;
  last_name?: string;
  team_role?: string;
};


type Handoff = {
  reason: string | null;
  priority: string | null;
  assigned_to: string | null;
  claimed_at: string | null;
};


type QueueEntry = {
  case: CaseData;
  booking: Booking | null;
  guest: Guest | null;
  property: Property | null;
  tasks: Task[];
  escalations: Escalation[];
  operator: Operator | null;
  handoff: Handoff;
  compensation_request:CompensationRequest | null;
  compensation_decision:CompensationDecision | null;
};

type CompensationRequest = {
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

type CompensationDecision = {
  compensation_decision_id: string;
  compensation_request_id: string;
  decision: string;
  amount: number | null;
  currency: string | null;
  reason: string;
  decided_by: string;
  created_at: string;
};

type CaseEvent = {
  case_event_id: string;
  case_id: string;
  event_type: string;
  actor_type: string;
  actor_id: string | null;
  summary: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

type ConversationMessage = {
  message_id: string;
  booking_id: string;
  guest_id: string;
  sender_type: string;
  message_text: string;
  channel: string;
  created_at: string;
};


const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

const DEMO_OPERATOR_ID = "GRO_254";

const TECHNICIANS = [
  {
    id: "MNT_904",
    name: "Thomas Moreau",
  },
  {
    id: "MNT_157",
    name: "Rachid Benali",
  },
  {
    id: "MNT_683",
    name: "Piotr Kowalski",
  },
  {
    id: "MNT_421",
    name: "Mamadou Diallo",
  },
];

function priorityClasses(
  priority: string | null
) {
  const normalized =
    priority?.toLowerCase();

  if (
    normalized === "critical" ||
    normalized === "high"
  ) {
    return "border-red-500/20 bg-red-500/10 text-red-300";
  }

  if (normalized === "medium") {
    return "border-amber-500/20 bg-amber-500/10 text-amber-300";
  }

  return "border-zinc-700 bg-zinc-800 text-zinc-300";
}


function operatorName(
  operator: Operator | null
) {
  if (!operator) {
    return "Unclaimed";
  }

  const name = [
    operator.first_name,
    operator.last_name,
  ]
    .filter(Boolean)
    .join(" ");

  return name || operator.team_id;
}

function formatEventTime(
  dateString: string
) {
  const date = new Date(
    dateString.replace(" ", "T") + "Z"
  );

  return date.toLocaleString(
    "en-GB",
    {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    }
  );
}


export default function OperationsPage() {
  const [
    queue,
    setQueue,
  ] = useState<QueueEntry[]>([]);

  const [
    selectedCaseId,
    setSelectedCaseId,
  ] = useState<string | null>(null);

  const [
    isLoading,
    setIsLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState<string | null>(null);

  const [
    timeline,
    setTimeline,
  ] = useState<CaseEvent[]>([]);

  const [
  conversation,
  setConversation,
] = useState<ConversationMessage[]>([]);

const [
  isConversationLoading,
  setIsConversationLoading,
] = useState(false);

  const [
    isTimelineLoading,
    setIsTimelineLoading,
  ] = useState(false);

  const [
    isActionLoading,
    setIsActionLoading,
  ] = useState(false);

  const [
    selectedWorkerId,
    setSelectedWorkerId,
  ] = useState("MNT_683");

  const [
    actionError,
    setActionError,
  ] = useState<string | null>(null);

  const [
    compensationAmount,
    setCompensationAmount,
    ] = useState("");

    const [
    compensationReason,
    setCompensationReason,
    ] = useState("");

    const [
    compensationCurrency,
    setCompensationCurrency,
    ] = useState("EUR");

  const loadQueue = useCallback(
    async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `${API_URL}/operations/queue`,
          {
            cache: "no-store",
          }
        );

        if (!response.ok) {
          throw new Error(
            `Queue request failed: ${response.status}`
          );
        }

        const data: QueueEntry[] =
          await response.json();

        setQueue(data);

        setSelectedCaseId(
          (current) => {
            if (
              current &&
              data.some(
                (entry) =>
                  entry.case.case_id ===
                  current
              )
            ) {
              return current;
            }

            return (
              data[0]?.case.case_id ??
              null
            );
          }
        );
      } catch (err) {
        console.error(err);

        setQueue([]);
        setSelectedCaseId(null);

        setError(
          "Unable to load the human operations queue."
        );
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

const loadConversation = useCallback(
  async (bookingId: string) => {
    setIsConversationLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/reservations/${bookingId}/messages`,
        {
          cache: "no-store",
        }
      );

      if (!response.ok) {
        throw new Error(
          `Conversation request failed: ${response.status}`
        );
      }

      const data: ConversationMessage[] =
        await response.json();

      setConversation(data);

    } catch (error) {
      console.error(
        "Unable to load conversation:",
        error
      );

      setConversation([]);

    } finally {
      setIsConversationLoading(false);
    }
  },
  []
);

const loadTimeline = useCallback(
  async (caseId: string) => {
    setIsTimelineLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/cases/${caseId}/timeline`
      );

      if (!response.ok) {
        throw new Error(
          `Timeline request failed: ${response.status}`
        );
      }

      const data: CaseEvent[] =
        await response.json();

      setTimeline(data);
    } catch (error) {
      console.error(
        "Unable to load Case timeline:",
        error
      );

      setTimeline([]);
    } finally {
      setIsTimelineLoading(false);
    }
  },
  []
);

async function returnCaseToAgent() {
  if (
    !selectedEntry ||
    isActionLoading
  ) {
    return;
  }

  setIsActionLoading(true);
  setActionError(null);

  try {
    const response = await fetch(
      `${API_URL}/cases/${selectedEntry.case.case_id}/return-to-agent`,
      {
        method: "PATCH",

        headers: {
          "Content-Type":
            "application/json",
        },

        body: JSON.stringify({
          operator_id:
            DEMO_OPERATOR_ID,
        }),
      }
    );

    const data =
      await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ??
          `Return failed: ${response.status}`
      );
    }

    await loadQueue();

    setTimeline([]);
  } catch (error) {
    console.error(error);

    setActionError(
      error instanceof Error
        ? error.message
        : "Unable to return Case to agent."
    );
  } finally {
    setIsActionLoading(false);
  }
}

async function resolveEscalation(
  escalationId: string
) {
  if (
    !selectedEntry ||
    isActionLoading
  ) {
    return;
  }

  setIsActionLoading(true);
  setActionError(null);

  try {
    const response = await fetch(
      `${API_URL}/escalations/${escalationId}/resolve`,
      {
        method: "PATCH",
        headers: {
        "Content-Type":
          "application/json",
         },

      body: JSON.stringify({
        operator_id:
          DEMO_OPERATOR_ID,
      }),
      
      }
    );

    const data =
      await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ??
          `Escalation resolution failed: ${response.status}`
      );
    }

    await Promise.all([
      loadQueue(),
      loadTimeline(
        selectedEntry.case.case_id
      ),
    ]);
  } catch (error) {
    console.error(error);

    setActionError(
      error instanceof Error
        ? error.message
        : "Unable to resolve escalation."
    );
  } finally {
    setIsActionLoading(false);
  }
}

async function submitCompensationDecision(
  decision: "approved" | "denied"
) {
  if (
    !selectedEntry ||
    !selectedEntry.compensation_request ||
    isActionLoading
  ) {
    return;
  }

  const reason =
    compensationReason.trim();

  if (!reason) {
    setActionError(
      "A decision reason is required."
    );
    return;
  }

  let amount: number | undefined;

  if (decision === "approved") {
    amount = Number(
      compensationAmount
    );

    if (
      !Number.isFinite(amount) ||
      amount <= 0
    ) {
      setActionError(
        "Enter a valid compensation amount."
      );
      return;
    }
  }

  setIsActionLoading(true);
  setActionError(null);

  try {
    const response = await fetch(
      `${API_URL}/compensation-requests/${selectedEntry.compensation_request.compensation_request_id}/decision`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body: JSON.stringify({
          decision,
          decided_by:
            DEMO_OPERATOR_ID,
          reason,

          ...(decision ===
          "approved"
            ? {
                amount,
                currency:
                  compensationCurrency,
              }
            : {}),
        }),
      }
    );

    const data =
      await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ??
          `Compensation decision failed: ${response.status}`
      );
    }

    await Promise.all([
      loadQueue(),
      loadTimeline(
        selectedEntry.case.case_id
      ),
    ]);

    setCompensationAmount("");
    setCompensationReason("");

  } catch (error) {
    console.error(error);

    setActionError(
      error instanceof Error
        ? error.message
        : "Unable to record compensation decision."
    );

  } finally {
    setIsActionLoading(false);
  }
}

async function completeTask(
  taskId: string
) {
  if (
    !selectedEntry ||
    isActionLoading
  ) {
    return;
  }

  setIsActionLoading(true);
  setActionError(null);

  try {
    const response = await fetch(
      `${API_URL}/tasks/${taskId}/complete`,
      {
        method: "PATCH",
        headers: {
        "Content-Type":
          "application/json",
        },

      body: JSON.stringify({
        operator_id:
          DEMO_OPERATOR_ID,
      }),
      }
    );

    const data =
      await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ??
          `Task completion failed: ${response.status}`
      );
    }

    await Promise.all([
      loadQueue(),
      loadTimeline(
        selectedEntry.case.case_id
      ),
    ]);
  } catch (error) {
    console.error(error);

    setActionError(
      error instanceof Error
        ? error.message
        : "Unable to complete task."
    );
  } finally {
    setIsActionLoading(false);
  }
}

async function assignTaskToWorker(
  taskId: string
) {
  if (
    !selectedEntry ||
    isActionLoading
  ) {
    return;
  }

  setIsActionLoading(true);
  setActionError(null);

  try {
    const response = await fetch(
      `${API_URL}/tasks/${taskId}/assign`,
      {
        method: "PATCH",

        headers: {
          "Content-Type":
            "application/json",
        },

        body: JSON.stringify({
          operator_id:
            DEMO_OPERATOR_ID,

          worker_id:
            selectedWorkerId,
        }),
      }
    );

    const data =
      await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ??
          `Task assignment failed: ${response.status}`
      );
    }

    await Promise.all([
      loadQueue(),
      loadTimeline(
        selectedEntry.case.case_id
      ),
    ]);
  } catch (error) {
    console.error(error);

    setActionError(
      error instanceof Error
        ? error.message
        : "Unable to assign technician."
    );
  } finally {
    setIsActionLoading(false);
  }
}

async function claimSelectedCase() {
  if (
    !selectedEntry ||
    isActionLoading
  ) {
    return;
  }

  setIsActionLoading(true);
  setActionError(null);

  try {
    const response = await fetch(
      `${API_URL}/cases/${selectedEntry.case.case_id}/claim`,
      {
        method: "PATCH",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({
          operator_id: DEMO_OPERATOR_ID,
        }),
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ??
          `Claim failed: ${response.status}`
      );
    }

    await Promise.all([
      loadQueue(),
      loadTimeline(
        selectedEntry.case.case_id
      ),
    ]);
  } catch (error) {
    console.error(error);

    setActionError(
      error instanceof Error
        ? error.message
        : "Unable to claim Case."
    );
  } finally {
    setIsActionLoading(false);
  }
}

useEffect(() => {
  const timer = window.setTimeout(() => {
    if (!selectedCaseId) {
      setTimeline([]);
      return;
    }

    void loadTimeline(selectedCaseId);
  }, 0);

  return () => {
    window.clearTimeout(timer);
  };
}, [
  selectedCaseId,
  loadTimeline,
]);


useEffect(() => {
  const timer = window.setTimeout(() => {
    void loadQueue();
  }, 0);

  return () => {
    window.clearTimeout(timer);
  };
}, [loadQueue]);


const selectedEntry =
  queue.find(
    (entry) =>
      entry.case.case_id ===
      selectedCaseId
  ) ?? null;


useEffect(() => {
  const timer = window.setTimeout(() => {
    if (!selectedEntry) {
      setConversation([]);
      return;
    }

    void loadConversation(
      selectedEntry.case.booking_id
    );
  }, 0);

  return () => {
    window.clearTimeout(timer);
  };
}, [
  selectedEntry,
  loadConversation,
]);

  const humanWorkComplete =
    selectedEntry !== null &&
    selectedEntry.tasks.every(
        (task) =>
        task.task_status !== "open"
    ) &&
    selectedEntry.escalations.every(
        (escalation) =>
        escalation.status !== "open"
    );


   


  const unclaimedCount =
    queue.filter(
      (entry) =>
        entry.case.assigned_to === null
    ).length;


  const claimedCount =
    queue.length - unclaimedCount;


  return (
    <main className="min-h-screen bg-[#09090b] text-zinc-100">

      {/* HEADER */}

      <header className="border-b border-zinc-800 bg-[#09090b]">

        <div className="mx-auto flex max-w-[1500px] items-center justify-between px-6 py-4">

          <div className="flex items-center gap-3">

            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-sm font-bold text-zinc-950">
              SO
            </div>

            <div>
              <h1 className="font-semibold tracking-tight">
                StayOps Operations
              </h1>

              <p className="text-xs text-zinc-500">
                Human intervention workspace
              </p>
            </div>

          </div>


          <div className="flex items-center gap-3">

            <Link
              href="/"
              className="rounded-lg border border-blue-500/30 bg-blue-500/10 px-4 py-2 text-xs font-semibold text-blue-300 transition hover:border-blue-400/50 hover:bg-blue-500/20 hover:text-blue-200"
            >
              Guest Demo
            </Link>

            <button
              onClick={() =>
                void loadQueue()
              }
              disabled={isLoading}
              className="rounded-lg bg-white px-4 py-2 text-xs font-semibold text-zinc-950 transition hover:bg-zinc-200 disabled:opacity-50"
            >
              {isLoading
                ? "Refreshing..."
                : "Refresh"}
            </button>

          </div>

        </div>

      </header>


      <div className="mx-auto max-w-[1500px] px-6 py-6">

        {/* SUMMARY */}

        <div className="mb-6 grid gap-4 md:grid-cols-3">

          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5">

            <p className="text-xs uppercase tracking-[0.18em] text-zinc-500">
              Waiting for human
            </p>

            <p className="mt-2 text-3xl font-semibold">
              {queue.length}
            </p>

          </div>


          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5">

            <p className="text-xs uppercase tracking-[0.18em] text-zinc-500">
              Unclaimed
            </p>

            <p className="mt-2 text-3xl font-semibold text-amber-300">
              {unclaimedCount}
            </p>

          </div>


          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5">

            <p className="text-xs uppercase tracking-[0.18em] text-zinc-500">
              Claimed
            </p>

            <p className="mt-2 text-3xl font-semibold text-emerald-300">
              {claimedCount}
            </p>

          </div>

        </div>


        {error && (

          <div className="mb-6 rounded-xl border border-red-900 bg-red-950/30 p-4 text-sm text-red-300">
            {error}
          </div>

        )}
        {actionError && (
          <div className="mb-6 rounded-xl border border-red-900 bg-red-950/30 p-4 text-sm text-red-300">
            {actionError}
          </div>
        )}


        {/* MAIN WORKSPACE */}

        <div className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">

          {/* QUEUE */}

          <section className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/60">

            <div className="border-b border-zinc-800 px-5 py-4">

              <p className="text-xs uppercase tracking-[0.18em] text-zinc-500">
                Human queue
              </p>

              <h2 className="mt-1 font-semibold">
                Cases requiring attention
              </h2>

            </div>


            <div className="max-h-[760px] overflow-y-auto">

              {isLoading &&
              queue.length === 0 ? (

                <div className="p-8 text-center text-sm text-zinc-500">
                  Loading queue...
                </div>

              ) : queue.length === 0 ? (

                <div className="p-10 text-center">

                  <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-300">
                    ✓
                  </div>

                  <p className="mt-4 text-sm font-medium">
                    Queue clear
                  </p>

                  <p className="mt-1 text-xs text-zinc-500">
                    No Cases are waiting for human action.
                  </p>

                </div>

              ) : (

                queue.map(
                  (entry) => {

                    const selected =
                      selectedCaseId ===
                      entry.case.case_id;

                    return (

                      <button
                        key={
                          entry.case.case_id
                        }
                        onClick={() =>
                          setSelectedCaseId(
                            entry.case.case_id
                          )
                        }
                        className={`w-full border-b border-zinc-800 p-5 text-left transition last:border-b-0 ${
                          selected
                            ? "bg-zinc-800/80"
                            : "hover:bg-zinc-800/40"
                        }`}
                      >

                        <div className="flex items-start justify-between gap-4">

                          <div>

                            <div className="flex items-center gap-2">

                              <span className="text-sm font-semibold capitalize">
                                {
                                  entry.case.category
                                }
                              </span>

                              <span
                                className={`rounded-full border px-2 py-0.5 text-[10px] font-medium capitalize ${priorityClasses(
                                  entry.handoff.priority
                                )}`}
                              >
                                {
                                  entry.handoff.priority ??
                                  "unknown"
                                }
                              </span>

                            </div>


                            <p className="mt-1 text-xs text-zinc-500">
                              {entry.guest
                                ? `${entry.guest.first_name} ${entry.guest.last_name}`
                                : entry.case.booking_id}
                            </p>

                          </div>


                          <span
                            className={
                              entry.operator
                                ? "rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2 py-1 text-[10px] text-emerald-300"
                                : "rounded-full border border-amber-500/20 bg-amber-500/10 px-2 py-1 text-[10px] text-amber-300"
                            }
                          >
                            {entry.operator
                              ? "Claimed"
                              : "Unclaimed"}
                          </span>

                        </div>


                        <p className="mt-3 line-clamp-2 text-xs leading-relaxed text-zinc-400">
                          {entry.case.summary ??
                            entry.handoff.reason ??
                            "Human intervention required."}
                        </p>


                        <div className="mt-4 flex items-center gap-4 text-[11px] text-zinc-600">

                          <span>
                            {entry.tasks.filter(
                              (task) =>
                                task.task_status ===
                                "open"
                            ).length}{" "}
                            open tasks
                          </span>

                          <span>
                            {
                              entry.escalations.filter(
                                (escalation) =>
                                  escalation.status ===
                                  "open"
                              ).length
                            }{" "}
                            escalations
                          </span>

                        </div>

                      </button>

                    );
                  }
                )

              )}

            </div>

          </section>


          {/* CASE PREVIEW */}

          <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60">

            {!selectedEntry ? (

              <div className="flex min-h-[500px] items-center justify-center text-sm text-zinc-500">
                Select a Case from the queue.
              </div>

            ) : (

              <div>

                <div className="border-b border-zinc-800 p-6">

                  <div className="flex items-start justify-between gap-6">

                    <div>

                      <p className="text-xs uppercase tracking-[0.18em] text-zinc-500">
                        {
                          selectedEntry.case.case_id
                        }
                      </p>

                      <h2 className="mt-2 text-xl font-semibold capitalize">
                        {
                          selectedEntry.case.category
                        }{" "}
                        Case
                      </h2>

                      <p className="mt-2 max-w-2xl text-sm leading-relaxed text-zinc-400">
                        {
                          selectedEntry.case.summary ??
                          selectedEntry.handoff.reason
                        }
                      </p>

                    </div>


                    <div className="flex items-center gap-3">

                    <span className="rounded-full border border-violet-500/20 bg-violet-500/10 px-3 py-1 text-xs text-violet-300">
                        waiting_human
                    </span>

                    {!selectedEntry.operator && (

                        <button
                        onClick={() =>
                            void claimSelectedCase()
                        }
                        disabled={isActionLoading}
                        className="rounded-lg bg-white px-4 py-2 text-xs font-semibold text-zinc-950 transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                        {isActionLoading
                            ? "Claiming..."
                            : "Claim Case"}
                        </button>

                    )}

                    </div>

                  </div>

                </div>


                <div className="grid gap-6 p-6 md:grid-cols-2">

                  {/* GUEST */}

                  <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-4">

                    <p className="text-[11px] uppercase tracking-wider text-zinc-600">
                      Guest
                    </p>

                    <p className="mt-2 font-medium">
                      {selectedEntry.guest
                        ? `${selectedEntry.guest.first_name} ${selectedEntry.guest.last_name}`
                        : "Unknown guest"}
                    </p>

                    <p className="mt-1 text-xs text-zinc-500">
                      {
                        selectedEntry.case.booking_id
                      }
                    </p>

                  </div>


                  {/* PROPERTY */}

                  <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-4">

                    <p className="text-[11px] uppercase tracking-wider text-zinc-600">
                      Property
                    </p>

                    <p className="mt-2 font-medium">
                      {
                        selectedEntry.property?.title ??
                        selectedEntry.case.property_id
                      }
                    </p>

                    <p className="mt-1 text-xs text-zinc-500">
                      {
                        selectedEntry.case.property_id
                      }
                    </p>

                  </div>


                  {/* OWNER */}

                  <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-4">

                    <p className="text-[11px] uppercase tracking-wider text-zinc-600">
                      Current owner
                    </p>

                    <p
                      className={`mt-2 font-medium ${
                        selectedEntry.operator
                          ? "text-emerald-300"
                          : "text-amber-300"
                      }`}
                    >
                      {operatorName(
                        selectedEntry.operator
                      )}
                    </p>

                    {selectedEntry.operator?.team_role && (

                      <p className="mt-1 text-xs text-zinc-500">
                        {
                          selectedEntry.operator.team_role
                        }
                      </p>

                    )}

                  </div>


                  {/* HANDOFF */}

                  <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-4">

                    <p className="text-[11px] uppercase tracking-wider text-zinc-600">
                      Handoff reason
                    </p>

                    <p className="mt-2 text-sm leading-relaxed text-zinc-300">
                      {
                        selectedEntry.handoff.reason ??
                        "Human intervention required."
                      }
                    </p>

                  </div>

                </div>
                
                {/* GUEST CONVERSATION */}

                <div className="border-t border-zinc-800 p-6">

                <div className="flex items-center justify-between">

                    <div>
                    <p className="text-[11px] uppercase tracking-[0.18em] text-zinc-600">
                        Booking conversation
                    </p>

                    <h3 className="mt-1 font-medium">
                        Guest Conversation
                    </h3>
                    </div>

                    <span className="rounded-full bg-zinc-800 px-2.5 py-1 text-xs text-zinc-400">
                    {conversation.length} messages
                    </span>

                </div>


                <div className="mt-5 max-h-[420px] space-y-4 overflow-y-auto">

                    {isConversationLoading ? (

                    <p className="text-sm text-zinc-500">
                        Loading conversation...
                    </p>

                    ) : conversation.length === 0 ? (

                    <div className="rounded-xl border border-dashed border-zinc-800 py-6 text-center">

                        <p className="text-sm text-zinc-500">
                        No conversation recorded.
                        </p>

                    </div>

                    ) : (

                    conversation.map((item) => {

                        const isGuest =
                        item.sender_type === "guest";

                        return (

                        <div
                            key={item.message_id}
                            className={
                            isGuest
                                ? "flex flex-col items-start"
                                : "flex flex-col items-end"
                            }
                        >

                            <span className="mb-1 px-1 text-[10px] font-medium uppercase tracking-wider text-zinc-600">
                            {isGuest
                                ? "Guest"
                                : "StayOps"}
                            </span>

                            <div
                            className={
                                isGuest
                                ? "max-w-[85%] rounded-xl border border-blue-500/20 bg-blue-500/10 px-4 py-3 text-sm leading-relaxed text-zinc-200"
                                : "max-w-[85%] rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm leading-relaxed text-zinc-300"
                            }
                            >
                            {item.message_text}
                            </div>

                        </div>

                        );
                    })

                    )}

                </div>

                </div>


                {/* FINANCIAL REVIEW */}

                {selectedEntry.compensation_request && (
                <div className="border-t border-zinc-800 p-6">

                    <div className="flex items-start justify-between gap-4">
                    <div>
                        <p className="text-[11px] uppercase tracking-[0.18em] text-zinc-600">
                        Financial workflow
                        </p>

                        <h3 className="mt-1 font-medium">
                        Compensation Review
                        </h3>
                    </div>

                    <span
                        className={`rounded-full border px-2.5 py-1 text-xs capitalize ${
                        selectedEntry.compensation_request.status ===
                        "pending_review"
                            ? "border-amber-500/20 bg-amber-500/10 text-amber-300"
                            : "border-emerald-500/20 bg-emerald-500/10 text-emerald-300"
                        }`}
                    >
                        {selectedEntry.compensation_request.status.replace(
                        "_",
                        " "
                        )}
                    </span>
                    </div>


                    <div className="mt-5 grid gap-4 md:grid-cols-2">

                    <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-4">
                        <p className="text-[11px] uppercase tracking-wider text-zinc-600">
                        Requested outcome
                        </p>

                        <p className="mt-2 text-sm text-zinc-200">
                        {selectedEntry.compensation_request
                            .requested_outcome ??
                            "Not specified"}
                        </p>
                    </div>


                    <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-4">
                        <p className="text-[11px] uppercase tracking-wider text-zinc-600">
                        Related Case
                        </p>

                        <p className="mt-2 font-mono text-xs text-zinc-400">
                        {selectedEntry.compensation_request
                            .related_case_id ??
                            "No related operational Case"}
                        </p>
                    </div>

                    </div>


                    <div className="mt-4 rounded-xl border border-zinc-800 bg-zinc-950/60 p-4">
                    <p className="text-[11px] uppercase tracking-wider text-zinc-600">
                        Guest request
                    </p>

                    <p className="mt-2 text-sm leading-relaxed text-zinc-300">
                        {selectedEntry.compensation_request.reason}
                    </p>
                    </div>


                    {selectedEntry.compensation_decision ? (

                    <div className="mt-4 rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-4">

                        <p className="text-[11px] uppercase tracking-wider text-emerald-400">
                        Final human decision
                        </p>

                        <p className="mt-2 text-lg font-semibold capitalize text-emerald-200">
                        {selectedEntry.compensation_decision.decision}
                        </p>

                        {selectedEntry.compensation_decision.amount !== null && (
                        <p className="mt-1 text-sm text-zinc-300">
                            {
                            selectedEntry.compensation_decision
                                .amount
                            }{" "}
                            {
                            selectedEntry.compensation_decision
                                .currency
                            }
                        </p>
                        )}

                        <p className="mt-3 text-sm text-zinc-400">
                        {
                            selectedEntry.compensation_decision
                            .reason
                        }
                        </p>

                        <p className="mt-2 text-xs text-zinc-600">
                        Decided by{" "}
                        {
                            selectedEntry.compensation_decision
                            .decided_by
                        }
                        </p>

                    </div>

                    ) : (

                    <div className="mt-5">

                        {!selectedEntry.operator ? (

                        <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 p-4 text-sm text-amber-200">
                            Claim this Case before making a financial decision.
                        </div>

                        ) : (

                        <>
                            <div className="grid gap-4 md:grid-cols-[1fr_140px]">

                            <div>
                                <label className="text-[11px] uppercase tracking-wider text-zinc-600">
                                Approved amount
                                </label>

                                <input
                                type="number"
                                min="0"
                                step="0.01"
                                value={compensationAmount}
                                onChange={(event) =>
                                    setCompensationAmount(
                                    event.target.value
                                    )
                                }
                                placeholder="150.00"
                                className="mt-2 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 outline-none focus:border-violet-500/60"
                                />
                            </div>


                            <div>
                                <label className="text-[11px] uppercase tracking-wider text-zinc-600">
                                Currency
                                </label>

                                <select
                                value={compensationCurrency}
                                onChange={(event) =>
                                    setCompensationCurrency(
                                    event.target.value
                                    )
                                }
                                className="mt-2 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 outline-none focus:border-violet-500/60"
                                >
                                <option value="EUR">EUR</option>
                                <option value="GBP">GBP</option>
                                <option value="USD">USD</option>
                                </select>
                            </div>

                            </div>


                            <div className="mt-4">
                            <label className="text-[11px] uppercase tracking-wider text-zinc-600">
                                Decision reason
                            </label>

                            <textarea
                                value={compensationReason}
                                onChange={(event) =>
                                setCompensationReason(
                                    event.target.value
                                )
                                }
                                rows={3}
                                placeholder="Explain why this compensation request is being approved or denied."
                                className="mt-2 w-full resize-none rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 outline-none focus:border-violet-500/60"
                            />
                            </div>


                            <div className="mt-4 flex flex-wrap gap-3">

                            <button
                                onClick={() =>
                                void submitCompensationDecision(
                                    "approved"
                                )
                                }
                                disabled={isActionLoading}
                                className="rounded-lg bg-emerald-500 px-4 py-2 text-xs font-semibold text-zinc-950 transition hover:bg-emerald-400 disabled:opacity-50"
                            >
                                {isActionLoading
                                ? "Saving..."
                                : "Approve Compensation"}
                            </button>


                            <button
                                onClick={() =>
                                void submitCompensationDecision(
                                    "denied"
                                )
                                }
                                disabled={isActionLoading}
                                className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-xs font-semibold text-red-300 transition hover:bg-red-500/20 disabled:opacity-50"
                            >
                                {isActionLoading
                                ? "Saving..."
                                : "Deny Request"}
                            </button>

                            </div>
                        </>

                        )}

                    </div>

                    )}

                </div>
                )}

                {/* RETURN TO AGENT */}

                {selectedEntry.operator &&
                humanWorkComplete && (

                    <div className="border-t border-zinc-800 p-6">

                    <div className="flex items-center justify-between gap-6 rounded-xl border border-violet-500/20 bg-violet-500/10 p-4">

                        <div>
                        <p className="text-sm font-medium text-violet-200">
                            Human work complete
                        </p>

                        <p className="mt-1 text-xs text-zinc-400">
                            All linked tasks and escalations are complete.
                            Control can return to the StayOps agent.
                        </p>
                        </div>

                        <button
                        onClick={() =>
                            void returnCaseToAgent()
                        }
                        disabled={isActionLoading}
                        className="shrink-0 rounded-lg bg-violet-500 px-4 py-2 text-xs font-semibold text-white transition hover:bg-violet-400 disabled:opacity-50"
                        >
                        {isActionLoading
                            ? "Returning..."
                            : "Return to Agent"}
                        </button>

                    </div>

                    </div>

                )}

                {/* TASKS */}

                <div className="border-t border-zinc-800 p-6">

                  <h3 className="font-medium">
                    Operational work
                  </h3>

                  <div className="mt-4 space-y-3">

                    {selectedEntry.tasks.length === 0 ? (

                      <p className="text-sm text-zinc-500">
                        No linked tasks.
                      </p>

                    ) : (

                      selectedEntry.tasks.map(
                    (task) => (

                        <div
                        key={task.task_id}
                        className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-4"
                        >

                        <div className="flex items-center justify-between gap-4">

                            <div>
                            <p className="text-sm font-medium">
                                {task.title}
                            </p>

                            <p className="mt-1 text-xs capitalize text-zinc-500">
                                {task.category}
                            </p>
                            </div>

                            <span className="rounded-full bg-zinc-800 px-2.5 py-1 text-xs capitalize text-zinc-300">
                            {task.task_status}
                            </span>

                        </div>


                        {/* TECHNICIAN ASSIGNMENT */}

                        {selectedEntry.operator &&
                            task.task_status === "open" && (

                            <div className="mt-4 border-t border-zinc-800 pt-4">

                                <p className="text-[11px] uppercase tracking-wider text-zinc-600">
                                Assigned technician
                                </p>

                                {task.assigned_to ? (

                                <div className="mt-2 flex items-center justify-between gap-4">

                                    <p className="text-sm font-medium text-emerald-300">
                                    {
                                        TECHNICIANS.find(
                                        (worker) =>
                                            worker.id ===
                                            task.assigned_to
                                        )?.name ??
                                        task.assigned_to
                                    }
                                    </p>

                                    <button
                                    onClick={() =>
                                        void completeTask(
                                        task.task_id
                                        )
                                    }
                                    disabled={isActionLoading}
                                    className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs font-semibold text-emerald-300 transition hover:bg-emerald-500/20 disabled:opacity-50"
                                    >
                                    {isActionLoading
                                        ? "Completing..."
                                        : "Mark Complete"}
                                    </button>

                                </div>

                                ) : (

                                <div className="mt-2 flex gap-2">

                                    <select
                                    value={selectedWorkerId}
                                    onChange={(event) =>
                                        setSelectedWorkerId(
                                        event.target.value
                                        )
                                    }
                                    className="flex-1 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-zinc-200 outline-none focus:border-violet-500/60"
                                    >
                                    {TECHNICIANS.map(
                                        (worker) => (

                                        <option
                                            key={worker.id}
                                            value={worker.id}
                                        >
                                            {worker.name}
                                        </option>

                                        )
                                    )}
                                    </select>

                                    <button
                                    onClick={() =>
                                        void assignTaskToWorker(
                                        task.task_id
                                        )
                                    }
                                    disabled={isActionLoading}
                                    className="rounded-lg bg-violet-500 px-3 py-2 text-xs font-semibold text-white transition hover:bg-violet-400 disabled:opacity-50"
                                    >
                                    {isActionLoading
                                        ? "Assigning..."
                                        : "Assign"}
                                    </button>

                                </div>

                                )}

                            </div>

                            )}

                        </div>

                    )
                    )

                    )}

                  </div>

                </div>


                {/* ESCALATIONS */}

                <div className="border-t border-zinc-800 p-6">

                  <h3 className="font-medium">
                    Escalations
                  </h3>

                  <div className="mt-4 space-y-3">

                    {selectedEntry.escalations.length ===
                    0 ? (

                      <p className="text-sm text-zinc-500">
                        No linked escalations.
                      </p>

                    ) : (

                      selectedEntry.escalations.map(
                        (escalation) => (

                          <div
                            key={
                              escalation.escalation_id
                            }
                            className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-4"
                          >

                            <div className="flex items-center justify-between gap-4">

                              <span className="text-sm font-medium capitalize">
                                {
                                  escalation.category
                                }
                              </span>

                              <span
                                className={`rounded-full border px-2.5 py-1 text-xs capitalize ${priorityClasses(
                                  escalation.priority
                                )}`}
                              >
                                {
                                  escalation.priority
                                }
                              </span>

                            </div>

                            <p className="mt-3 text-sm leading-relaxed text-zinc-400">
                              {
                                escalation.reason
                              }
                            </p>
                            {selectedEntry.operator &&
                            escalation.status === "open" && (

                                <div className="mt-4 border-t border-zinc-800 pt-4">

                                <button
                                    onClick={() =>
                                    void resolveEscalation(
                                        escalation.escalation_id
                                    )
                                    }
                                    disabled={isActionLoading}
                                    className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs font-semibold text-emerald-300 transition hover:bg-emerald-500/20 disabled:opacity-50"
                                >
                                    {isActionLoading
                                    ? "Resolving..."
                                    : "Resolve Escalation"}
                                </button>

                                </div>

                            )}

                          </div>

                          

                        )
                      )

                    )}

                  </div>

                </div>

                {/* CASE TIMELINE */}

                <div className="border-t border-zinc-800 p-6">

                <div className="flex items-center justify-between">

                    <div>
                    <p className="text-[11px] uppercase tracking-[0.18em] text-zinc-600">
                        Audit trail
                    </p>

                    <h3 className="mt-1 font-medium">
                        Case Timeline
                    </h3>
                    </div>

                    <span className="rounded-full bg-zinc-800 px-2.5 py-1 text-xs text-zinc-400">
                    {timeline.length} events
                    </span>

                </div>


                <div className="mt-5">

                    {isTimelineLoading ? (

                    <p className="text-sm text-zinc-500">
                        Loading timeline...
                    </p>

                    ) : timeline.length === 0 ? (

                    <div className="rounded-xl border border-dashed border-zinc-800 py-6 text-center">

                        <p className="text-sm text-zinc-500">
                        No Case events recorded.
                        </p>

                    </div>

                    ) : (

                    timeline.map(
                        (event, index) => (

                        <div
                            key={
                            event.case_event_id
                            }
                            className="relative flex gap-4 pb-6 last:pb-0"
                        >

                            {index <
                            timeline.length - 1 && (

                            <div className="absolute left-[7px] top-5 h-full w-px bg-zinc-800" />

                            )}


                            <div className="relative z-10 mt-1.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-violet-500/40 bg-violet-500/10">

                            <div className="h-1.5 w-1.5 rounded-full bg-violet-400" />

                            </div>


                            <div className="min-w-0 flex-1">

                            <div className="flex flex-wrap items-center justify-between gap-2">

                                <p className="text-sm font-medium text-zinc-200">
                                {event.summary}
                                </p>

                                <span className="text-[11px] text-zinc-600">
                                {formatEventTime(
                                    event.created_at
                                )}
                                </span>

                            </div>


                            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-zinc-500">

                                <span className="capitalize">
                                {event.actor_type}
                                </span>

                                {event.actor_id && (
                                <>
                                    <span>·</span>

                                    <span>
                                    {event.actor_id}
                                    </span>
                                </>
                                )}

                                <span>·</span>

                                <span className="font-mono text-[11px] text-zinc-600">
                                {event.event_type}
                                </span>

                            </div>

                            </div>

                        </div>

                        )
                    )

                    )}

                </div>

                </div>

              </div>

            )}

          </section>

        </div>

      </div>

    </main>
  );
}