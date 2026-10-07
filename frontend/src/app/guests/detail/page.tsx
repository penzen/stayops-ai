"use client";

import Link from "next/link";
import {
  useCallback,
  useEffect,
  useState,
} from "react";
import { useRouter } from "next/navigation";

import { demoFetch } from "../../../lib/demo-session";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

type GuestDetail = {
  guest: {
    guest_id: string;
    first_name: string;
    last_name: string;
    email: string | null;
    phone: string | null;
    guest_lang: string;
    locale: string;
    guest_geo: string | null;
  };
  reservation: {
    booking_id: string;
    property_id: string;
    check_in: string;
    check_out: string;
    nights: number;
    total_price: number;
    book_status: string;
    source: string | null;
  };
  property: {
    property_id: string;
    title: string;
    city: string | null;
    prop_address: string | null;
  };
  resource_kind: string;
  operational_status:
    | "needs_human"
    | "active_issue"
    | "clear";
  metrics: {
    active_cases: number;
    waiting_human: number;
    open_tasks: number;
    open_escalations: number;
    pending_financial_reviews: number;
    messages: number;
  };
  cases: Array<{
    case_id: string;
    category: string;
    status: string;
    summary: string | null;
    assigned_to: string | null;
    claimed_at: string | null;
    created_at: string;
  }>;
  tasks: Array<{
    task_id: string;
    category: string;
    title: string;
    task_status: string;
    assigned_to: string | null;
    task_date: string;
  }>;
  escalations: Array<{
    escalation_id: string;
    category: string;
    reason: string;
    priority: string;
    status: string;
    assigned_to: string | null;
    created_at: string;
  }>;
  messages: Array<{
    message_id: string;
    sender_type: string;
    message_text: string;
    created_at: string;
  }>;
  compensation: Array<{
    compensation_request_id: string;
    status: string;
    reason: string;
    requested_outcome: string | null;
    created_at: string;
    decision: string | null;
    amount: number | null;
    currency: string | null;
  }>;
};

function titleCase(value: string) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase()
    );
}

function statusClasses(value: string) {
  if (
    value === "needs_human" ||
    value === "waiting_human"
  ) {
    return "border-amber-500/20 bg-amber-500/10 text-amber-300";
  }

  if (
    value === "active_issue" ||
    value === "in_progress" ||
    value === "open"
  ) {
    return "border-blue-500/20 bg-blue-500/10 text-blue-300";
  }

  if (
    value === "resolved" ||
    value === "clear" ||
    value === "approved"
  ) {
    return "border-emerald-500/20 bg-emerald-500/10 text-emerald-300";
  }

  return "border-zinc-700 bg-zinc-800 text-zinc-300";
}

function formatDate(value: string) {
  const date = new Date(
    value.replace(" ", "T")
  );

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString(
    undefined,
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }
  );
}

export default function GuestDetailPage() {
  const router = useRouter();

  const [data, setData] =
    useState<GuestDetail | null>(null);
  const [isLoading, setIsLoading] =
    useState(true);
  const [error, setError] =
    useState<string | null>(null);

  const loadGuest = useCallback(
    async (id: string) => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await demoFetch(
          `${API_URL}/demo/sessions/guests/${encodeURIComponent(
            id
          )}`,
          {
            cache: "no-store",
          }
        );

        if (!response.ok) {
          throw new Error(
            `Guest detail request failed: ${response.status}`
          );
        }

        const detail: GuestDetail =
          await response.json();

        setData(detail);
      } catch (loadError) {
        console.error(loadError);
        setError(
          "Unable to load this guest."
        );
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    const timer =
      window.setTimeout(() => {
        const params =
          new URLSearchParams(
            window.location.search
          );

        const guestId =
          params.get("guest_id");

        if (!guestId) {
          setIsLoading(false);
          setError(
            "No guest was selected."
          );
          return;
        }

        void loadGuest(guestId);
      }, 0);

    return () => {
      window.clearTimeout(timer);
    };
  }, [loadGuest]);

  const waitingHumanCase =
    data?.cases.find(
      (item) =>
        item.status ===
        "waiting_human"
    ) ?? null;

  function openGuestOps() {
    if (!data) {
      return;
    }

    window.localStorage.setItem(
      "stayops:selectedBookingId",
      data.reservation.booking_id
    );

    router.push("/guest-ops");
  }

  if (
    isLoading &&
    !data &&
    !error
  ) {
    return (
      <main className="min-h-screen bg-[#09090b] text-zinc-100">
        <div className="mx-auto max-w-[1450px] px-6 py-8">
          <div className="h-48 animate-pulse rounded-2xl border border-zinc-800 bg-zinc-900/50" />
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#09090b] text-zinc-100">
      <div className="mx-auto max-w-[1450px] px-6 py-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <Link
              href="/guests"
              className="text-xs font-medium text-zinc-600 transition hover:text-zinc-300"
            >
              ← Guest directory
            </Link>

            <p className="mt-5 text-xs font-semibold uppercase tracking-[0.18em] text-blue-300">
              Guest detail
            </p>

            <h1 className="mt-2 text-2xl font-semibold tracking-tight">
              {data
                ? `${data.guest.first_name} ${data.guest.last_name}`
                : "Guest unavailable"}
            </h1>
          </div>

          {data && (
            <div className="flex flex-wrap gap-2">
              {waitingHumanCase && (
                <Link
                  href={`/operations?case_id=${encodeURIComponent(
                    waitingHumanCase.case_id
                  )}`}
                  className="rounded-lg border border-violet-500/20 bg-violet-500/10 px-4 py-2.5 text-xs font-semibold text-violet-200 transition hover:bg-violet-500/15"
                >
                  Open Operations
                </Link>
              )}

              <button
                onClick={openGuestOps}
                className="rounded-lg bg-white px-4 py-2.5 text-xs font-semibold text-zinc-950 transition hover:bg-zinc-200"
              >
                Open in Guest Ops
              </button>
            </div>
          )}
        </div>

        {error && (
          <div className="mt-6 rounded-xl border border-red-900/70 bg-red-950/20 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {data && (
          <>
            <div className="mt-7 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
              <section className="rounded-2xl border border-zinc-800 bg-zinc-900/45 p-5">
                <div className="flex items-start justify-between gap-5">
                  <div>
                    <p className="text-sm font-semibold text-zinc-200">
                      Guest profile
                    </p>
                    <p className="mt-1 text-xs text-zinc-600">
                      Session-owned fictional guest.
                    </p>
                  </div>

                  <span
                    className={[
                      "rounded-full border px-2.5 py-1 text-[10px] font-medium",
                      statusClasses(
                        data.operational_status
                      ),
                    ].join(" ")}
                  >
                    {titleCase(
                      data.operational_status
                    )}
                  </span>
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-2">
                  {[
                    ["Guest ID", data.guest.guest_id],
                    ["Language", data.guest.guest_lang.toUpperCase()],
                    ["Email", data.guest.email ?? "Not provided"],
                    ["Phone", data.guest.phone ?? "Not provided"],
                  ].map(([label, value]) => (
                    <div
                      key={label}
                      className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3"
                    >
                      <p className="text-[10px] uppercase tracking-wider text-zinc-700">
                        {label}
                      </p>
                      <p className="mt-2 break-all text-xs font-medium text-zinc-400">
                        {value}
                      </p>
                    </div>
                  ))}
                </div>
              </section>

              <section className="rounded-2xl border border-zinc-800 bg-zinc-900/45 p-5">
                <p className="text-sm font-semibold text-zinc-200">
                  Current stay
                </p>

                <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  <div className="sm:col-span-2">
                    <p className="text-[10px] uppercase tracking-wider text-zinc-700">
                      Property
                    </p>
                    <p className="mt-2 text-sm font-medium text-zinc-300">
                      {data.property.title}
                    </p>
                    <p className="mt-1 text-xs text-zinc-600">
                      {data.property.city ??
                        data.property.prop_address ??
                        data.property.property_id}
                    </p>
                  </div>

                  <div>
                    <p className="text-[10px] uppercase tracking-wider text-zinc-700">
                      Check-in
                    </p>
                    <p className="mt-2 text-xs font-medium text-zinc-400">
                      {formatDate(
                        data.reservation.check_in
                      )}
                    </p>
                  </div>

                  <div>
                    <p className="text-[10px] uppercase tracking-wider text-zinc-700">
                      Check-out
                    </p>
                    <p className="mt-2 text-xs font-medium text-zinc-400">
                      {formatDate(
                        data.reservation.check_out
                      )}
                    </p>
                  </div>
                </div>

                <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
                  {[
                    ["Active Cases", data.metrics.active_cases],
                    ["Waiting human", data.metrics.waiting_human],
                    ["Open tasks", data.metrics.open_tasks],
                    ["Handoffs", data.metrics.open_escalations],
                    ["Financial", data.metrics.pending_financial_reviews],
                    ["Messages", data.metrics.messages],
                  ].map(([label, value]) => (
                    <div
                      key={label}
                      className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3"
                    >
                      <p className="text-[9px] uppercase tracking-wider text-zinc-700">
                        {label}
                      </p>
                      <p className="mt-2 text-xl font-semibold text-white">
                        {value}
                      </p>
                    </div>
                  ))}
                </div>
              </section>
            </div>

            <div className="mt-6 grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
              <section className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/40">
                <div className="border-b border-zinc-800 px-5 py-4">
                  <p className="text-sm font-semibold text-zinc-200">
                    Cases
                  </p>
                  <p className="mt-1 text-xs text-zinc-600">
                    Operational history for this stay.
                  </p>
                </div>

                {data.cases.length ? (
                  <div className="divide-y divide-zinc-800">
                    {data.cases.map(
                      (item) => (
                        <div
                          key={item.case_id}
                          className="px-5 py-4"
                        >
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="text-xs font-semibold text-zinc-300">
                              {titleCase(
                                item.category
                              )}
                            </p>
                            <span
                              className={[
                                "rounded-full border px-2 py-0.5 text-[9px] font-medium",
                                statusClasses(
                                  item.status
                                ),
                              ].join(" ")}
                            >
                              {titleCase(
                                item.status
                              )}
                            </span>
                          </div>

                          <p className="mt-2 text-xs leading-5 text-zinc-500">
                            {item.summary ??
                              "Operational Case"}
                          </p>
                        </div>
                      )
                    )}
                  </div>
                ) : (
                  <div className="px-5 py-10 text-center text-xs text-zinc-600">
                    No Cases for this stay.
                  </div>
                )}
              </section>

              <section className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/40">
                <div className="border-b border-zinc-800 px-5 py-4">
                  <p className="text-sm font-semibold text-zinc-200">
                    Recent conversation
                  </p>
                  <p className="mt-1 text-xs text-zinc-600">
                    Latest guest and agent messages.
                  </p>
                </div>

                {data.messages.length ? (
                  <div className="space-y-3 p-5">
                    {data.messages.map(
                      (message) => (
                        <div
                          key={message.message_id}
                          className={[
                            "rounded-xl border px-4 py-3",
                            message.sender_type ===
                            "guest"
                              ? "border-blue-500/20 bg-blue-500/10"
                              : "border-zinc-800 bg-zinc-950/70",
                          ].join(" ")}
                        >
                          <p className="text-[9px] font-semibold uppercase tracking-wider text-zinc-600">
                            {message.sender_type}
                          </p>
                          <p className="mt-2 text-xs leading-5 text-zinc-300">
                            {message.message_text}
                          </p>
                        </div>
                      )
                    )}
                  </div>
                ) : (
                  <div className="px-5 py-10 text-center text-xs text-zinc-600">
                    No messages yet.
                  </div>
                )}
              </section>
            </div>

            <div className="mt-6 grid gap-6 lg:grid-cols-3">
              <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
                <p className="text-sm font-semibold text-zinc-200">
                  Tasks
                </p>
                <div className="mt-4 space-y-3">
                  {data.tasks.length ? (
                    data.tasks.map(
                      (task) => (
                        <div
                          key={task.task_id}
                          className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3"
                        >
                          <p className="text-xs font-medium text-zinc-300">
                            {task.title}
                          </p>
                          <p className="mt-1 text-[10px] text-zinc-600">
                            {titleCase(
                              task.category
                            )}
                            {" · "}
                            {titleCase(
                              task.task_status
                            )}
                          </p>
                        </div>
                      )
                    )
                  ) : (
                    <p className="text-xs text-zinc-600">
                      No tasks.
                    </p>
                  )}
                </div>
              </section>

              <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
                <p className="text-sm font-semibold text-zinc-200">
                  Escalations
                </p>
                <div className="mt-4 space-y-3">
                  {data.escalations.length ? (
                    data.escalations.map(
                      (item) => (
                        <div
                          key={item.escalation_id}
                          className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3"
                        >
                          <div className="flex items-center justify-between gap-3">
                            <p className="text-xs font-medium text-zinc-300">
                              {titleCase(
                                item.category
                              )}
                            </p>
                            <span className="text-[9px] font-semibold uppercase tracking-wider text-amber-300">
                              {item.priority}
                            </span>
                          </div>
                          <p className="mt-2 text-[11px] leading-4 text-zinc-600">
                            {item.reason}
                          </p>
                        </div>
                      )
                    )
                  ) : (
                    <p className="text-xs text-zinc-600">
                      No escalations.
                    </p>
                  )}
                </div>
              </section>

              <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
                <p className="text-sm font-semibold text-zinc-200">
                  Financial review
                </p>
                <div className="mt-4 space-y-3">
                  {data.compensation.length ? (
                    data.compensation.map(
                      (item) => (
                        <div
                          key={
                            item.compensation_request_id
                          }
                          className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3"
                        >
                          <div className="flex items-center justify-between gap-3">
                            <p className="text-xs font-medium text-zinc-300">
                              {titleCase(
                                item.status
                              )}
                            </p>
                            {item.decision && (
                              <span
                                className={[
                                  "rounded-full border px-2 py-0.5 text-[9px]",
                                  statusClasses(
                                    item.decision
                                  ),
                                ].join(" ")}
                              >
                                {titleCase(
                                  item.decision
                                )}
                              </span>
                            )}
                          </div>
                          <p className="mt-2 text-[11px] leading-4 text-zinc-600">
                            {item.reason}
                          </p>
                        </div>
                      )
                    )
                  ) : (
                    <p className="text-xs text-zinc-600">
                      No financial review.
                    </p>
                  )}
                </div>
              </section>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
