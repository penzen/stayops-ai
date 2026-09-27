import type {
  CompensationEvidence,
  QueueEntry,
} from "../types";


type FinancialReviewProps = {
  entry: QueueEntry;

  evidence:
    CompensationEvidence | null;

  isEvidenceLoading: boolean;

  evidenceError:
    string | null;

  compensationAmount: string;
  compensationReason: string;
  compensationCurrency: string;

  isActionLoading: boolean;

  onAmountChange: (
    value: string
  ) => void;

  onReasonChange: (
    value: string
  ) => void;

  onCurrencyChange: (
    value: string
  ) => void;

  onDecision: (
    decision:
      "approved" | "denied"
  ) => void;
};


export default function FinancialReview({
  entry,
  evidence,
  isEvidenceLoading,
  evidenceError,
  compensationAmount,
  compensationReason,
  compensationCurrency,
  isActionLoading,
  onAmountChange,
  onReasonChange,
  onCurrencyChange,
  onDecision,
}: FinancialReviewProps) {

  if (!entry.compensation_request) {
    return null;
  }

  const request =
    entry.compensation_request;

  const decision =
    entry.compensation_decision;


  return (
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
            request.status ===
            "pending_review"
              ? "border-amber-500/20 bg-amber-500/10 text-amber-300"
              : "border-emerald-500/20 bg-emerald-500/10 text-emerald-300"
          }`}
        >
          {request.status.replace(
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
            {
              request.requested_outcome ??
              "Not specified"
            }
          </p>

        </div>


        <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-4">

          <p className="text-[11px] uppercase tracking-wider text-zinc-600">
            Related Case
          </p>

          <p className="mt-2 font-mono text-xs text-zinc-400">
            {
              request.related_case_id ??
              "No related operational Case"
            }
          </p>

        </div>

      </div>


      <div className="mt-4 rounded-xl border border-zinc-800 bg-zinc-950/60 p-4">

        <p className="text-[11px] uppercase tracking-wider text-zinc-600">
          Guest request
        </p>

        <p className="mt-2 text-sm leading-relaxed text-zinc-300">
          {request.reason}
        </p>

      </div>


      {/* FINANCIAL EVIDENCE */}

      <div className="mt-5 rounded-xl border border-violet-500/20 bg-violet-500/5 p-4">

        <div className="flex items-center justify-between gap-4">

          <div>

            <p className="text-[11px] uppercase tracking-[0.18em] text-violet-400">
              Decision evidence
            </p>

            <p className="mt-1 text-xs text-zinc-500">
              Operational facts linked to this compensation request.
            </p>

          </div>


          {evidence && (

            <span className="rounded-full border border-zinc-700 bg-zinc-900 px-2.5 py-1 text-xs text-zinc-400">

              {
                evidence
                  .operational_evidence
                  .task_count
              }{" "}
              tasks ·{" "}
              {
                evidence
                  .operational_evidence
                  .escalation_count
              }{" "}
              escalations

            </span>

          )}

        </div>


        {isEvidenceLoading ? (

          <p className="mt-4 text-sm text-zinc-500">
            Loading financial evidence...
          </p>

        ) : evidenceError ? (

          <p className="mt-4 text-sm text-red-300">
            {evidenceError}
          </p>

        ) : evidence ? (

          <div className="mt-4 space-y-4">


            {/* OPERATIONAL CASE */}

            <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-4">

              <p className="text-[11px] uppercase tracking-wider text-zinc-600">
                Related operational Case
              </p>


              {evidence.related_case ? (

                <>

                  <div className="mt-2 flex flex-wrap items-center gap-2">

                    <span className="text-sm font-medium capitalize text-zinc-200">
                      {
                        evidence
                          .related_case
                          .category
                      }
                    </span>

                    <span className="rounded-full bg-zinc-800 px-2 py-1 text-xs capitalize text-zinc-400">
                      {
                        evidence
                          .related_case
                          .status
                          .replace(
                            "_",
                            " "
                          )
                      }
                    </span>

                  </div>


                  <p className="mt-3 text-sm leading-relaxed text-zinc-400">
                    {
                      evidence
                        .related_case
                        .summary ??
                      "No operational summary recorded."
                    }
                  </p>

                </>

              ) : (

                <p className="mt-2 text-sm text-zinc-500">
                  No related operational Case.
                </p>

              )}

            </div>


            {/* BOOKING + PROPERTY */}

            <div className="grid gap-4 md:grid-cols-2">

              <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-4">

                <p className="text-[11px] uppercase tracking-wider text-zinc-600">
                  Booking
                </p>

                <p className="mt-2 font-mono text-xs text-zinc-400">
                  {
                    evidence
                      .booking
                      ?.booking_id ??
                    "Unknown booking"
                  }
                </p>


                {evidence
                  .booking
                  ?.total_price !==
                  undefined && (

                  <p className="mt-2 text-sm text-zinc-300">
                    Stay value:{" "}
                    {
                      evidence
                        .booking
                        .total_price
                    }{" "}
                    EUR
                  </p>

                )}

              </div>


              <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-4">

                <p className="text-[11px] uppercase tracking-wider text-zinc-600">
                  Property
                </p>

                <p className="mt-2 text-sm text-zinc-300">
                  {
                    evidence
                      .property
                      ?.title ??
                    evidence
                      .property
                      ?.property_id ??
                    "Unknown property"
                  }
                </p>


                {evidence
                  .property
                  ?.prop_address && (

                  <p className="mt-1 text-xs text-zinc-500">
                    {
                      evidence
                        .property
                        .prop_address
                    }
                  </p>

                )}

              </div>

            </div>


            {/* TASK EVIDENCE */}

            <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-4">

              <div className="flex items-center justify-between">

                <p className="text-[11px] uppercase tracking-wider text-zinc-600">
                  Operational tasks
                </p>

                <span className="text-xs text-zinc-500">
                  {
                    evidence
                      .operational_evidence
                      .open_task_count
                  }{" "}
                  open
                </span>

              </div>


              <div className="mt-3 space-y-2">

                {evidence
                  .operational_evidence
                  .tasks.length === 0 ? (

                  <p className="text-sm text-zinc-500">
                    No linked operational tasks.
                  </p>

                ) : (

                  evidence
                    .operational_evidence
                    .tasks.map(
                      (task) => (

                        <div
                          key={
                            task.task_id
                          }
                          className="flex items-center justify-between gap-3 rounded-lg bg-zinc-900 px-3 py-2"
                        >

                          <span className="text-sm text-zinc-300">
                            {task.title}
                          </span>

                          <span className="text-xs capitalize text-zinc-500">
                            {
                              task.task_status
                            }
                          </span>

                        </div>

                      )
                    )

                )}

              </div>

            </div>


            {/* ESCALATION EVIDENCE */}

            <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-4">

              <div className="flex items-center justify-between">

                <p className="text-[11px] uppercase tracking-wider text-zinc-600">
                  Operational escalations
                </p>

                <span className="text-xs text-zinc-500">
                  {
                    evidence
                      .operational_evidence
                      .open_escalation_count
                  }{" "}
                  open
                </span>

              </div>


              <div className="mt-3 space-y-2">

                {evidence
                  .operational_evidence
                  .escalations.length === 0 ? (

                  <p className="text-sm text-zinc-500">
                    No linked escalations.
                  </p>

                ) : (

                  evidence
                    .operational_evidence
                    .escalations.map(
                      (escalation) => (

                        <div
                          key={
                            escalation
                              .escalation_id
                          }
                          className="rounded-lg bg-zinc-900 px-3 py-2"
                        >

                          <div className="flex items-center justify-between gap-3">

                            <span className="text-sm capitalize text-zinc-300">
                              {
                                escalation
                                  .category
                              }
                            </span>

                            <span className="text-xs capitalize text-zinc-500">
                              {
                                escalation
                                  .status
                              }
                            </span>

                          </div>


                          <p className="mt-1 text-xs text-zinc-500">
                            {
                              escalation
                                .reason
                            }
                          </p>

                        </div>

                      )
                    )

                )}

              </div>

            </div>

          </div>

        ) : null}

      </div>


      {/* FINAL DECISION */}

      {decision ? (

        <div className="mt-4 rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-4">

          <p className="text-[11px] uppercase tracking-wider text-emerald-400">
            Final human decision
          </p>

          <p className="mt-2 text-lg font-semibold capitalize text-emerald-200">
            {decision.decision}
          </p>


          {decision.amount !== null && (

            <p className="mt-1 text-sm text-zinc-300">
              {
                decision.amount
              }{" "}
              {
                decision.currency
              }
            </p>

          )}


          <p className="mt-3 text-sm text-zinc-400">
            {decision.reason}
          </p>

          <p className="mt-2 text-xs text-zinc-600">
            Decided by{" "}
            {
              decision.decided_by
            }
          </p>

        </div>

      ) : (

        <div className="mt-5">

          {!entry.operator ? (

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
                    value={
                      compensationAmount
                    }
                    onChange={(
                      event
                    ) =>
                      onAmountChange(
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
                    value={
                      compensationCurrency
                    }
                    onChange={(
                      event
                    ) =>
                      onCurrencyChange(
                        event.target.value
                      )
                    }
                    className="mt-2 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 outline-none focus:border-violet-500/60"
                  >
                    <option value="EUR">
                      EUR
                    </option>

                    <option value="GBP">
                      GBP
                    </option>

                    <option value="USD">
                      USD
                    </option>

                  </select>

                </div>

              </div>


              <div className="mt-4">

                <label className="text-[11px] uppercase tracking-wider text-zinc-600">
                  Decision reason
                </label>

                <textarea
                  value={
                    compensationReason
                  }
                  onChange={(
                    event
                  ) =>
                    onReasonChange(
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
                    void onDecision(
                      "approved"
                    )
                  }
                  disabled={
                    isActionLoading
                  }
                  className="rounded-lg bg-emerald-500 px-4 py-2 text-xs font-semibold text-zinc-950 transition hover:bg-emerald-400 disabled:opacity-50"
                >
                  {isActionLoading
                    ? "Saving..."
                    : "Approve Compensation"}
                </button>


                <button
                  onClick={() =>
                    void onDecision(
                      "denied"
                    )
                  }
                  disabled={
                    isActionLoading
                  }
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
  );
}