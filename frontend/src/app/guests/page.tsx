"use client";

import Link from "next/link";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import { demoFetch } from "../../lib/demo-session";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

type GuestDirectoryItem = {
  guest_id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  guest_lang: string;
  locale: string;
  booking_id: string;
  property_id: string;
  property_title: string;
  city: string | null;
  check_in: string;
  check_out: string;
  book_status: string;
  resource_kind: string;
  active_case_count: number;
  waiting_human_count: number;
  open_task_count: number;
  open_escalation_count: number;
  pending_financial_reviews: number;
  message_count: number;
  last_message_at: string | null;
  operational_status:
    | "needs_human"
    | "active_issue"
    | "clear";
};

function languageLabel(value: string) {
  if (value === "en") return "English";
  if (value === "de") return "Deutsch";
  if (value === "fr") return "Français";
  return value.toUpperCase();
}

function statusLabel(
  value: GuestDirectoryItem["operational_status"]
) {
  if (value === "needs_human") {
    return "Needs human";
  }

  if (value === "active_issue") {
    return "Active issue";
  }

  return "Clear";
}

function statusClasses(
  value: GuestDirectoryItem["operational_status"]
) {
  if (value === "needs_human") {
    return "border-amber-500/20 bg-amber-500/10 text-amber-300";
  }

  if (value === "active_issue") {
    return "border-blue-500/20 bg-blue-500/10 text-blue-300";
  }

  return "border-emerald-500/20 bg-emerald-500/10 text-emerald-300";
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

export default function GuestsPage() {
  const [guests, setGuests] =
    useState<GuestDirectoryItem[]>([]);
  const [query, setQuery] =
    useState("");
  const [filter, setFilter] =
    useState<
      "all" | "attention" | "active" | "clear"
    >("all");
  const [isLoading, setIsLoading] =
    useState(true);
  const [error, setError] =
    useState<string | null>(null);

  const loadGuests = useCallback(
    async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await demoFetch(
          `${API_URL}/demo/sessions/guests`,
          {
            cache: "no-store",
          }
        );

        if (!response.ok) {
          throw new Error(
            `Guest directory request failed: ${response.status}`
          );
        }

        const data:
          GuestDirectoryItem[] =
            await response.json();

        setGuests(data);
      } catch (loadError) {
        console.error(loadError);
        setError(
          "Unable to load the guest directory."
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
        void loadGuests();
      }, 0);

    return () => {
      window.clearTimeout(timer);
    };
  }, [loadGuests]);

  const filteredGuests = useMemo(
    () => {
      const normalizedQuery =
        query.trim().toLowerCase();

      return guests.filter((guest) => {
        const matchesQuery =
          !normalizedQuery ||
          [
            guest.first_name,
            guest.last_name,
            guest.email ?? "",
            guest.booking_id,
            guest.property_title,
            guest.city ?? "",
          ]
            .join(" ")
            .toLowerCase()
            .includes(normalizedQuery);

        if (!matchesQuery) {
          return false;
        }

        if (filter === "attention") {
          return (
            guest.operational_status ===
            "needs_human"
          );
        }

        if (filter === "active") {
          return (
            guest.operational_status ===
            "active_issue"
          );
        }

        if (filter === "clear") {
          return (
            guest.operational_status ===
            "clear"
          );
        }

        return true;
      });
    },
    [guests, query, filter]
  );

  const attentionCount =
    guests.filter(
      (guest) =>
        guest.operational_status ===
        "needs_human"
    ).length;

  const activeIssueCount =
    guests.filter(
      (guest) =>
        guest.operational_status ===
        "active_issue"
    ).length;

  return (
    <main className="min-h-screen bg-[#09090b] text-zinc-100">
      <div className="mx-auto max-w-[1450px] px-6 py-8">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-300">
              Guests
            </p>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight">
              Guest directory
            </h1>
            <p className="mt-2 text-sm leading-relaxed text-zinc-500">
              Session-scoped guests, current reservations and operational
              state in one place.
            </p>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() =>
                void loadGuests()
              }
              disabled={isLoading}
              className="rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2.5 text-xs font-semibold text-zinc-200 transition hover:border-zinc-600 hover:bg-zinc-800 disabled:opacity-50"
            >
              {isLoading
                ? "Refreshing..."
                : "Refresh"}
            </button>

            <Link
              href="/create-demo"
              className="inline-flex items-center justify-center rounded-lg bg-white px-4 py-2.5 text-xs font-semibold text-zinc-950 transition hover:bg-zinc-200"
            >
              Create guest
            </Link>
          </div>
        </div>

        <div className="mt-7 grid gap-3 sm:grid-cols-3">
          <section className="rounded-2xl border border-zinc-800 bg-zinc-900/45 p-4">
            <p className="text-[11px] uppercase tracking-[0.14em] text-zinc-600">
              Session guests
            </p>
            <p className="mt-3 text-3xl font-semibold text-white">
              {isLoading && guests.length === 0
                ? "—"
                : guests.length}
            </p>
          </section>

          <section className="rounded-2xl border border-zinc-800 bg-zinc-900/45 p-4">
            <p className="text-[11px] uppercase tracking-[0.14em] text-zinc-600">
              Needs human
            </p>
            <p className="mt-3 text-3xl font-semibold text-amber-300">
              {attentionCount}
            </p>
          </section>

          <section className="rounded-2xl border border-zinc-800 bg-zinc-900/45 p-4">
            <p className="text-[11px] uppercase tracking-[0.14em] text-zinc-600">
              Active issues
            </p>
            <p className="mt-3 text-3xl font-semibold text-blue-300">
              {activeIssueCount}
            </p>
          </section>
        </div>

        <div className="mt-6 flex flex-col gap-3 rounded-2xl border border-zinc-800 bg-zinc-900/40 p-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="relative w-full max-w-xl">
            <input
              value={query}
              onChange={(event) =>
                setQuery(
                  event.target.value
                )
              }
              placeholder="Search guest, booking or property"
              className="w-full rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm outline-none transition placeholder:text-zinc-700 focus:border-blue-500/50"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            {[
              ["all", "All"],
              ["attention", "Needs human"],
              ["active", "Active issue"],
              ["clear", "Clear"],
            ].map(([value, label]) => (
              <button
                key={value}
                onClick={() =>
                  setFilter(
                    value as typeof filter
                  )
                }
                className={[
                  "rounded-lg border px-3 py-2 text-xs font-medium transition",
                  filter === value
                    ? "border-zinc-600 bg-zinc-800 text-white"
                    : "border-zinc-800 bg-zinc-950 text-zinc-500 hover:text-zinc-300",
                ].join(" ")}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="mt-5 rounded-xl border border-red-900/70 bg-red-950/20 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        <section className="mt-5 overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/40">
          <div className="hidden grid-cols-[1.25fr_1.25fr_0.8fr_0.8fr_auto] gap-4 border-b border-zinc-800 px-5 py-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-zinc-700 lg:grid">
            <span>Guest</span>
            <span>Reservation</span>
            <span>Status</span>
            <span>Activity</span>
            <span />
          </div>

          {isLoading && guests.length === 0 ? (
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
          ) : filteredGuests.length ? (
            <div className="divide-y divide-zinc-800">
              {filteredGuests.map(
                (guest) => (
                  <div
                    key={guest.guest_id}
                    className="grid gap-4 px-5 py-4 transition hover:bg-zinc-900/70 lg:grid-cols-[1.25fr_1.25fr_0.8fr_0.8fr_auto] lg:items-center"
                  >
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="truncate text-sm font-semibold text-zinc-200">
                          {guest.first_name}{" "}
                          {guest.last_name}
                        </p>

                        {guest.resource_kind ===
                          "custom" && (
                          <span className="rounded-full border border-violet-500/20 bg-violet-500/10 px-1.5 py-0.5 text-[8px] font-semibold uppercase tracking-wider text-violet-300">
                            custom
                          </span>
                        )}
                      </div>

                      <p className="mt-1 truncate text-xs text-zinc-600">
                        {languageLabel(
                          guest.guest_lang
                        )}
                        {guest.email
                          ? ` · ${guest.email}`
                          : ""}
                      </p>
                    </div>

                    <div className="min-w-0">
                      <p className="truncate text-xs font-medium text-zinc-300">
                        {guest.property_title}
                      </p>
                      <p className="mt-1 truncate text-[11px] text-zinc-600">
                        {formatDate(
                          guest.check_in
                        )}
                        {" → "}
                        {formatDate(
                          guest.check_out
                        )}
                        {guest.city
                          ? ` · ${guest.city}`
                          : ""}
                      </p>
                    </div>

                    <div>
                      <span
                        className={[
                          "inline-flex rounded-full border px-2.5 py-1 text-[10px] font-medium",
                          statusClasses(
                            guest.operational_status
                          ),
                        ].join(" ")}
                      >
                        {statusLabel(
                          guest.operational_status
                        )}
                      </span>
                    </div>

                    <div className="text-[11px] leading-5 text-zinc-500">
                      <p>
                        {guest.active_case_count} Cases
                        {" · "}
                        {guest.open_task_count} tasks
                      </p>
                      <p className="text-zinc-700">
                        {guest.message_count} messages
                        {" · "}
                        {guest.open_escalation_count} handoffs
                      </p>
                    </div>

                    <Link
                      href={`/guests/detail?guest_id=${encodeURIComponent(
                        guest.guest_id
                      )}`}
                      className="inline-flex items-center justify-center rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs font-medium text-zinc-300 transition hover:border-zinc-600 hover:bg-zinc-800"
                    >
                      View guest
                    </Link>
                  </div>
                )
              )}
            </div>
          ) : (
            <div className="flex min-h-64 items-center justify-center px-6 text-center">
              <div>
                <p className="text-sm font-medium text-zinc-300">
                  No guests match this view
                </p>
                <p className="mt-2 text-xs text-zinc-600">
                  Try another status filter or search term.
                </p>
              </div>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
