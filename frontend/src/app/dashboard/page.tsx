"use client";

import Link from "next/link";
import {
  useCallback,
  useEffect,
  useState,
} from "react";
import { useRouter } from "next/navigation";

import { demoFetch } from "../../lib/demo-session";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

type DashboardMetrics = {
  active_stays: number;
  active_cases: number;
  waiting_human: number;
  open_tasks: number;
  open_escalations: number;
  pending_financial_reviews: number;
};

type AttentionCase = {
  case_id: string;
  booking_id: string;
  category: string;
  status: string;
  summary: string | null;
  assigned_to: string | null;
  created_at: string;
  first_name: string;
  last_name: string;
  property_title: string;
  priority: string | null;
  open_task_count: number;
  open_escalation_count: number;
  pending_financial_review: number;
};

type SessionStay = {
  booking_id: string;
  guest_id: string;
  property_id: string;
  first_name: string;
  last_name: string;
  guest_lang: string;
  property_title: string;
  book_status: string;
  resource_kind: string;
  active_case_count: number;
  message_count: number;
};

type DashboardData = {
  session: {
    session_id: string;
    expires_at: string;
  };
  metrics: DashboardMetrics;
  attention: AttentionCase[];
  stays: SessionStay[];
  generated_at: string;
};

function titleCase(value: string) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase()
    );
}

function languageLabel(value: string) {
  if (value === "en") return "English";
  if (value === "de") return "Deutsch";
  if (value === "fr") return "Français";
  return value.toUpperCase();
}

function statusClasses(status: string) {
  if (status === "waiting_human") {
    return "border-amber-500/20 bg-amber-500/10 text-amber-300";
  }

  if (status === "in_progress") {
    return "border-blue-500/20 bg-blue-500/10 text-blue-300";
  }

  if (status === "waiting_guest") {
    return "border-violet-500/20 bg-violet-500/10 text-violet-300";
  }

  return "border-zinc-700 bg-zinc-800 text-zinc-300";
}

function priorityClasses(
  priority: string | null
) {
  if (
    priority === "high" ||
    priority === "critical"
  ) {
    return "text-red-300";
  }

  if (priority === "medium") {
    return "text-amber-300";
  }

  return "text-zinc-500";
}

function expiryLabel(value: string) {
  const normalized =
    value.includes("T")
      ? value
      : value.replace(" ", "T");

  const date = new Date(
    `${normalized}Z`
  );

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleTimeString(
    undefined,
    {
      hour: "2-digit",
      minute: "2-digit",
    }
  );
}

export default function DashboardPage() {
  const router = useRouter();

  const [data, setData] =
    useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] =
    useState(true);
  const [error, setError] =
    useState<string | null>(null);

  const loadOverview = useCallback(
    async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await demoFetch(
          `${API_URL}/demo/sessions/overview`,
          {
            cache: "no-store",
          }
        );

        if (!response.ok) {
          throw new Error(
            `Overview request failed: ${response.status}`
          );
        }

        const overview: DashboardData =
          await response.json();

        setData(overview);
      } catch (loadError) {
        console.error(loadError);
        setError(
          "Unable to load the StayOps overview."
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
        void loadOverview();
      }, 0);

    return () => {
      window.clearTimeout(timer);
    };
  }, [loadOverview]);

  function openStay(
    bookingId: string
  ) {
    window.localStorage.setItem(
      "stayops:selectedBookingId",
      bookingId
    );

    router.push("/guest-ops");
  }

  const metrics = data?.metrics;

  const cards = [
    {
      label: "Active stays",
      value: metrics?.active_stays ?? 0,
      hint: "Session-owned reservations",
    },
    {
      label: "Active Cases",
      value: metrics?.active_cases ?? 0,
      hint: "Unresolved operational Cases",
    },
    {
      label: "Waiting on human",
      value: metrics?.waiting_human ?? 0,
      hint: "Cases blocked on operator action",
    },
    {
      label: "Open tasks",
      value: metrics?.open_tasks ?? 0,
      hint: "Operational work still open",
    },
    {
      label: "Open escalations",
      value:
        metrics?.open_escalations ?? 0,
      hint: "Human handoffs still open",
    },
    {
      label: "Financial review",
      value:
        metrics?.pending_financial_reviews ??
        0,
      hint: "Refund decisions awaiting review",
    },
  ];

  return (
    <main className="min-h-screen bg-[#09090b] text-zinc-100">
      <div className="mx-auto max-w-[1450px] px-6 py-8">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-300">
              Overview
            </p>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight">
              StayOps command center
            </h1>
            <p className="mt-2 text-sm leading-relaxed text-zinc-500">
              A session-scoped view of guest activity, operational Cases and
              work currently requiring attention.
            </p>
          </div>

          <button
            onClick={() =>
              void loadOverview()
            }
            disabled={isLoading}
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2.5 text-xs font-semibold text-zinc-200 transition hover:border-zinc-600 hover:bg-zinc-800 disabled:opacity-50"
          >
            {isLoading
              ? "Refreshing..."
              : "Refresh overview"}
          </button>
        </div>

        {error && (
          <div className="mt-6 rounded-xl border border-red-900/70 bg-red-950/20 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        <div className="mt-7 grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
          {cards.map((card) => (
            <section
              key={card.label}
              className="rounded-2xl border border-zinc-800 bg-zinc-900/45 p-4"
            >
              <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-zinc-600">
                {card.label}
              </p>

              <p className="mt-3 text-3xl font-semibold tracking-tight text-white">
                {isLoading && !data
                  ? "—"
                  : card.value}
              </p>

              <p className="mt-2 text-[11px] leading-4 text-zinc-600">
                {card.hint}
              </p>
            </section>
          ))}
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-[1.4fr_0.85fr]">
          <section className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/40">
            <div className="flex items-center justify-between border-b border-zinc-800 px-5 py-4">
              <div>
                <p className="text-sm font-semibold text-zinc-200">
                  Active Case activity
                </p>
                <p className="mt-1 text-xs text-zinc-600">
                  Unresolved Cases in this demo session.
                </p>
              </div>

              <Link
                href="/operations"
                className="text-xs font-medium text-zinc-500 transition hover:text-zinc-200"
              >
                Open Operations →
              </Link>
            </div>

            {isLoading && !data ? (
              <div className="space-y-3 p-5">
                {[1, 2, 3].map(
                  (item) => (
                    <div
                      key={item}
                      className="h-24 animate-pulse rounded-xl border border-zinc-800 bg-zinc-950/60"
                    />
                  )
                )}
              </div>
            ) : data?.attention.length ? (
              <div className="divide-y divide-zinc-800">
                {data.attention.map(
                  (item) => (
                    <div
                      key={item.case_id}
                      className="px-5 py-4"
                    >
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-sm font-semibold text-zinc-200">
                              {titleCase(
                                item.category
                              )}
                            </span>

                            <span
                              className={[
                                "rounded-full border px-2 py-0.5 text-[10px] font-medium",
                                statusClasses(
                                  item.status
                                ),
                              ].join(" ")}
                            >
                              {titleCase(
                                item.status
                              )}
                            </span>

                            {item.priority && (
                              <span
                                className={[
                                  "text-[10px] font-semibold uppercase tracking-wider",
                                  priorityClasses(
                                    item.priority
                                  ),
                                ].join(" ")}
                              >
                                {item.priority}
                              </span>
                            )}
                          </div>

                          <p className="mt-2 truncate text-xs text-zinc-500">
                            {item.first_name}{" "}
                            {item.last_name}
                            <span className="mx-2 text-zinc-800">
                              ·
                            </span>
                            {item.property_title}
                          </p>

                          <p className="mt-2 text-xs leading-5 text-zinc-400">
                            {item.summary ??
                              "Operational Case requires attention."}
                          </p>
                        </div>

                        <div className="flex shrink-0 gap-2 text-[10px] text-zinc-600">
                          <span className="rounded-lg border border-zinc-800 bg-zinc-950 px-2.5 py-1.5">
                            {item.open_task_count} tasks
                          </span>
                          <span className="rounded-lg border border-zinc-800 bg-zinc-950 px-2.5 py-1.5">
                            {item.open_escalation_count} handoffs
                          </span>
                          {Boolean(
                            item.pending_financial_review
                          ) && (
                            <span className="rounded-lg border border-violet-500/20 bg-violet-500/10 px-2.5 py-1.5 text-violet-300">
                              financial
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                )}
              </div>
            ) : (
              <div className="flex min-h-72 items-center justify-center px-6 text-center">
                <div className="max-w-sm">
                  <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-xl border border-emerald-500/20 bg-emerald-500/10 text-emerald-300">
                    ✓
                  </div>
                  <p className="mt-4 text-sm font-medium text-zinc-300">
                    No active Cases
                  </p>
                  <p className="mt-2 text-xs leading-5 text-zinc-600">
                    Send a guest issue from Guest Ops and the resulting
                    operational state will appear here.
                  </p>
                </div>
              </div>
            )}
          </section>

          <div className="space-y-6">
            <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
              <div className="flex items-start justify-between gap-5">
                <div>
                  <p className="text-sm font-semibold text-zinc-200">
                    Demo session
                  </p>
                  <p className="mt-1 text-xs text-zinc-600">
                    Isolated from other public visitors.
                  </p>
                </div>

                <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-emerald-300">
                  Protected
                </span>
              </div>

              <div className="mt-5 grid grid-cols-2 gap-3">
                <div className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-3">
                  <p className="text-[10px] uppercase tracking-wider text-zinc-700">
                    Session
                  </p>
                  <p className="mt-2 truncate text-xs font-medium text-zinc-400">
                    {data?.session.session_id ??
                      "Loading…"}
                  </p>
                </div>

                <div className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-3">
                  <p className="text-[10px] uppercase tracking-wider text-zinc-700">
                    Expires
                  </p>
                  <p className="mt-2 text-xs font-medium text-zinc-400">
                    {data
                      ? expiryLabel(
                          data.session.expires_at
                        )
                      : "Loading…"}
                  </p>
                </div>
              </div>
            </section>

            <section className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/40">
              <div className="border-b border-zinc-800 px-5 py-4">
                <p className="text-sm font-semibold text-zinc-200">
                  Session stays
                </p>
                <p className="mt-1 text-xs text-zinc-600">
                  Guests available in this isolated demo.
                </p>
              </div>

              <div className="divide-y divide-zinc-800">
                {data?.stays.map(
                  (stay) => (
                    <button
                      key={stay.booking_id}
                      onClick={() =>
                        openStay(
                          stay.booking_id
                        )
                      }
                      className="block w-full px-5 py-4 text-left transition hover:bg-zinc-900/80"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="truncate text-xs font-semibold text-zinc-300">
                              {stay.first_name}{" "}
                              {stay.last_name}
                            </p>

                            {stay.resource_kind ===
                              "custom" && (
                              <span className="rounded-full border border-violet-500/20 bg-violet-500/10 px-1.5 py-0.5 text-[8px] font-semibold uppercase tracking-wider text-violet-300">
                                custom
                              </span>
                            )}
                          </div>

                          <p className="mt-1 truncate text-[11px] text-zinc-600">
                            {stay.property_title}
                          </p>
                        </div>

                        <div className="shrink-0 text-right">
                          <p className="text-[10px] font-medium text-zinc-500">
                            {languageLabel(
                              stay.guest_lang
                            )}
                          </p>
                          <p className="mt-1 text-[10px] text-zinc-700">
                            {stay.active_case_count} Cases
                            {" · "}
                            {stay.message_count} messages
                          </p>
                        </div>
                      </div>
                    </button>
                  )
                )}

                {!isLoading &&
                  data?.stays.length === 0 && (
                    <div className="px-5 py-8 text-center text-xs text-zinc-600">
                      No session stays are available.
                    </div>
                  )}
              </div>
            </section>
          </div>
        </div>
      </div>
    </main>
  );
}
