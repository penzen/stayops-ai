"use client";
import Timeline from "./components/Timeline";
import TaskPanel from "./components/TaskPanel";
import Link from "next/link";
import EscalationPanel from "./components/EscalationPanel";
import QueueList from "./components/QueueList";
import ConversationPanel from "./components/ConversationPanel";
import FinancialReview from "./components/FinancialReview";
import {
  useCallback,
  useEffect,
  useState,
} from "react";
import CaseOverview from "./components/CaseOverview";
import {
  API_URL,
  DEMO_OPERATOR_ID,
} from "./constants";

import type {
  CaseEvent,
  CompensationEvidence,
  ConversationMessage,
  QueueEntry,
  Technician,
} from "./types";

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
    technicians,
    setTechnicians,
  ] = useState<Technician[]>([]);

  const [
    compensationEvidence,
    setCompensationEvidence,
  ] = useState<CompensationEvidence | null>(
    null
  );

  const [
    isCompensationEvidenceLoading,
    setIsCompensationEvidenceLoading,
  ] = useState(false);

  const [
    compensationEvidenceError,
    setCompensationEvidenceError,
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
  ] = useState("");

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



const loadTechnicians = useCallback(
  async () => {
    try {
      const response = await fetch(
        `${API_URL}/operations/technicians`,
        {
          cache: "no-store",
        }
      );

      if (!response.ok) {
        throw new Error(
          `Technicians request failed: ${response.status}`
        );
      }

      const data: Technician[] =
        await response.json();

      setTechnicians(data);

      setSelectedWorkerId(
        (current) => {
          if (
            current &&
            data.some(
              (worker) =>
                worker.team_id === current
            )
          ) {
            return current;
          }

          return (
            data[0]?.team_id ??
            ""
          );
        }
      );
    } catch (error) {
      console.error(
        "Unable to load technicians:",
        error
      );

      setTechnicians([]);
      setSelectedWorkerId("");
    }
  },
  []
);

useEffect(() => {
  const timer = window.setTimeout(() => {
    void loadTechnicians();
  }, 0);

  return () => {
    window.clearTimeout(timer);
  };
}, [loadTechnicians]);

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

const loadCompensationEvidence = useCallback(
  async (
    compensationRequestId: string
  ) => {
    setIsCompensationEvidenceLoading(
      true
    );

    setCompensationEvidenceError(
      null
    );

    try {
      const response = await fetch(
        `${API_URL}/compensation-requests/${compensationRequestId}/evidence`,
        {
          cache: "no-store",
        }
      );

      if (!response.ok) {
        throw new Error(
          `Compensation evidence request failed: ${response.status}`
        );
      }

      const data: CompensationEvidence =
        await response.json();

      setCompensationEvidence(data);

    } catch (error) {
      console.error(
        "Unable to load compensation evidence:",
        error
      );

      setCompensationEvidence(null);

      setCompensationEvidenceError(
        "Unable to load financial evidence."
      );

    } finally {
      setIsCompensationEvidenceLoading(
        false
      );
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

      loadCompensationEvidence(
        selectedEntry
          .compensation_request
          .compensation_request_id
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
    !selectedWorkerId ||
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



const selectedCompensationRequestId =
  selectedEntry
    ?.compensation_request
    ?.compensation_request_id ??
  null;

useEffect(() => {
  const timer = window.setTimeout(() => {
    if (!selectedCompensationRequestId) {
      setCompensationEvidence(null);
      setCompensationEvidenceError(null);
      return;
    }

    void loadCompensationEvidence(
      selectedCompensationRequestId
    );
  }, 0);

  return () => {
    window.clearTimeout(timer);
  };
}, [
  selectedCompensationRequestId,
  loadCompensationEvidence,
]);


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

          <QueueList
        queue={queue}
        isLoading={isLoading}
        selectedCaseId={
          selectedCaseId
        }
        onSelectCase={
          setSelectedCaseId
        }
        />

       


          {/* CASE PREVIEW */}

          <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60">

            {!selectedEntry ? (

              <div className="flex min-h-[500px] items-center justify-center text-sm text-zinc-500">
                Select a Case from the queue.
              </div>

            ) : ( 
            <>

              <CaseOverview
                entry={selectedEntry}
                isActionLoading={isActionLoading}
                onClaimCase={claimSelectedCase}
              />

             
                
                {/* GUEST CONVERSATION */}

                <ConversationPanel
                  conversation={conversation}
                  isLoading={isConversationLoading}
                />

                {/* FINANCIAL REVIEW */}
                <FinancialReview
                  entry={selectedEntry}
                  evidence={compensationEvidence}
                  isEvidenceLoading={
                    isCompensationEvidenceLoading
                  }
                  evidenceError={
                    compensationEvidenceError
                  }
                  compensationAmount={
                    compensationAmount
                  }
                  compensationReason={
                    compensationReason
                  }
                  compensationCurrency={
                    compensationCurrency
                  }
                  isActionLoading={
                    isActionLoading
                  }
                  onAmountChange={
                    setCompensationAmount
                  }
                  onReasonChange={
                    setCompensationReason
                  }
                  onCurrencyChange={
                    setCompensationCurrency
                  }
                  onDecision={
                    submitCompensationDecision
                  }
                />

               

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
                            All human work linked directly to this Case is complete.
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
  
                <TaskPanel
                  entry={selectedEntry}
                  technicians={technicians}
                  selectedWorkerId={
                    selectedWorkerId
                  }
                  isActionLoading={
                    isActionLoading
                  }
                  onWorkerChange={
                    setSelectedWorkerId
                  }
                  onAssignTask={
                    assignTaskToWorker
                  }
                  onCompleteTask={
                    completeTask
                  }
                />

                {/* ESCALATIONS */}

                <EscalationPanel
                entry={selectedEntry}
                isActionLoading={
                  isActionLoading
                }
                onResolveEscalation={
                  resolveEscalation
                }
              />

                {/* CASE TIMELINE */}

                <Timeline
                  timeline={timeline}
                  isLoading={isTimelineLoading}
                />                        
              </>    
            )}

          </section>

        </div>

      </div>

    </main>
  );
}