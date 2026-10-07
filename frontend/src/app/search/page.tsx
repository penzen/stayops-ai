"use client";

import Link from "next/link";
import {
  FormEvent,
  useCallback,
  useEffect,
  useState,
} from "react";
import { useRouter } from "next/navigation";

import { demoFetch } from "../../lib/demo-session";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

type GuestResult = {
  guest_id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  guest_lang: string;
  locale: string;
  booking_id: string;
  property_id: string;
  book_status: string;
  property_title: string;
  city: string | null;
  resource_kind: string;
};

type BookingResult = {
  booking_id: string;
  guest_id: string;
  property_id: string;
  check_in: string;
  check_out: string;
  book_status: string;
  first_name: string;
  last_name: string;
  property_title: string;
  city: string | null;
  resource_kind: string;
};

type CaseResult = {
  case_id: string;
  booking_id: string;
  property_id: string;
  category: string;
  status: string;
  summary: string | null;
  assigned_to: string | null;
  created_at: string;
  guest_id: string;
  first_name: string;
  last_name: string;
  property_title: string;
  priority: string | null;
};

type SearchResponse = {
  query: string;
  total: number;
  guests: GuestResult[];
  bookings: BookingResult[];
  cases: CaseResult[];
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
    value === "waiting_human" ||
    value === "high" ||
    value === "critical"
  ) {
    return "border-amber-500/20 bg-amber-500/10 text-amber-300";
  }

  if (
    value === "in_progress" ||
    value === "open"
  ) {
    return "border-blue-500/20 bg-blue-500/10 text-blue-300";
  }

  if (value === "resolved") {
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

export default function SearchPage() {
  const router = useRouter();

  const [query, setQuery] =
    useState("");
  const [result, setResult] =
    useState<SearchResponse | null>(null);
  const [isLoading, setIsLoading] =
    useState(false);
  const [error, setError] =
    useState<string | null>(null);

  const runSearch = useCallback(
    async (value: string) => {
      const normalized =
        value.trim();

      if (normalized.length < 2) {
        setResult({
          query: normalized,
          total: 0,
          guests: [],
          bookings: [],
          cases: [],
        });
        setError(null);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const response = await demoFetch(
          `${API_URL}/demo/sessions/search?q=${encodeURIComponent(
            normalized
          )}`,
          {
            cache: "no-store",
          }
        );

        if (!response.ok) {
          throw new Error(
            `Search request failed: ${response.status}`
          );
        }

        const data: SearchResponse =
          await response.json();

        setResult(data);
      } catch (searchError) {
        console.error(searchError);
        setError(
          "Unable to search this demo session."
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

        const initial =
          params.get("q") ?? "";

        setQuery(initial);

        if (initial.trim()) {
          void runSearch(initial);
        }
      }, 0);

    return () => {
      window.clearTimeout(timer);
    };
  }, [runSearch]);

  function submit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const normalized =
      query.trim();

    router.replace(
      normalized
        ? `/search?q=${encodeURIComponent(
            normalized
          )}`
        : "/search"
    );

    void runSearch(normalized);
  }

  function openBooking(
    bookingId: string
  ) {
    window.localStorage.setItem(
      "stayops:selectedBookingId",
      bookingId
    );

    router.push("/guest-ops");
  }

  const hasSearched =
    result !== null;

  return (
    <main className="min-h-screen bg-[#09090b] text-zinc-100">
      <div className="mx-auto max-w-[1450px] px-6 py-8">
        <div className="max-w-3xl">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-300">
            Global search
          </p>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight">
            Search guests, stays and Cases
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-zinc-500">
            Results are restricted to the current isolated demo session.
          </p>
        </div>

        <form
          onSubmit={submit}
          className="mt-7 flex max-w-3xl gap-3"
        >
          <input
            autoFocus
            value={query}
            onChange={(event) =>
              setQuery(
                event.target.value
              )
            }
            placeholder="Try Emma, heating, a booking ID or property name"
            className="min-w-0 flex-1 rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm outline-none transition placeholder:text-zinc-700 focus:border-violet-500/50"
          />

          <button
            type="submit"
            disabled={isLoading}
            className="rounded-xl bg-white px-5 py-3 text-sm font-semibold text-zinc-950 transition hover:bg-zinc-200 disabled:opacity-50"
          >
            {isLoading
              ? "Searching..."
              : "Search"}
          </button>
        </form>

        <p className="mt-3 text-[11px] text-zinc-700">
          Enter at least 2 characters.
        </p>

        {error && (
          <div className="mt-5 rounded-xl border border-red-900/70 bg-red-950/20 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {hasSearched && !error && (
          <div className="mt-7">
            <div className="flex items-center justify-between gap-4">
              <p className="text-sm font-medium text-zinc-300">
                {result.total} result
                {result.total === 1
                  ? ""
                  : "s"}
                {result.query
                  ? ` for “${result.query}”`
                  : ""}
              </p>
            </div>

            {result.total === 0 ? (
              <section className="mt-4 flex min-h-72 items-center justify-center rounded-2xl border border-zinc-800 bg-zinc-900/40 px-6 text-center">
                <div className="max-w-sm">
                  <p className="text-sm font-medium text-zinc-300">
                    No matches found
                  </p>
                  <p className="mt-2 text-xs leading-5 text-zinc-600">
                    Search by guest name, email, booking ID, property, Case category or Case summary.
                  </p>
                </div>
              </section>
            ) : (
              <div className="mt-4 space-y-6">
                {result.guests.length > 0 && (
                  <section className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/40">
                    <div className="border-b border-zinc-800 px-5 py-4">
                      <p className="text-sm font-semibold text-zinc-200">
                        Guests
                      </p>
                    </div>

                    <div className="divide-y divide-zinc-800">
                      {result.guests.map(
                        (guest) => (
                          <Link
                            key={guest.guest_id}
                            href={`/guests/detail?guest_id=${encodeURIComponent(
                              guest.guest_id
                            )}`}
                            className="flex items-center justify-between gap-5 px-5 py-4 transition hover:bg-zinc-900/80"
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
                                {guest.email ??
                                  guest.guest_id}
                                {" · "}
                                {guest.property_title}
                              </p>
                            </div>

                            <span className="shrink-0 text-xs text-zinc-600">
                              View guest →
                            </span>
                          </Link>
                        )
                      )}
                    </div>
                  </section>
                )}

                {result.bookings.length > 0 && (
                  <section className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/40">
                    <div className="border-b border-zinc-800 px-5 py-4">
                      <p className="text-sm font-semibold text-zinc-200">
                        Reservations
                      </p>
                    </div>

                    <div className="divide-y divide-zinc-800">
                      {result.bookings.map(
                        (booking) => (
                          <button
                            key={booking.booking_id}
                            onClick={() =>
                              openBooking(
                                booking.booking_id
                              )
                            }
                            className="flex w-full items-center justify-between gap-5 px-5 py-4 text-left transition hover:bg-zinc-900/80"
                          >
                            <div className="min-w-0">
                              <p className="truncate text-sm font-semibold text-zinc-200">
                                {booking.booking_id}
                              </p>
                              <p className="mt-1 truncate text-xs text-zinc-600">
                                {booking.first_name}{" "}
                                {booking.last_name}
                                {" · "}
                                {booking.property_title}
                              </p>
                              <p className="mt-1 text-[10px] text-zinc-700">
                                {formatDate(
                                  booking.check_in
                                )}
                                {" → "}
                                {formatDate(
                                  booking.check_out
                                )}
                              </p>
                            </div>

                            <span className="shrink-0 text-xs text-zinc-600">
                              Open Guest Ops →
                            </span>
                          </button>
                        )
                      )}
                    </div>
                  </section>
                )}

                {result.cases.length > 0 && (
                  <section className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/40">
                    <div className="border-b border-zinc-800 px-5 py-4">
                      <p className="text-sm font-semibold text-zinc-200">
                        Cases
                      </p>
                    </div>

                    <div className="divide-y divide-zinc-800">
                      {result.cases.map(
                        (item) => (
                          <Link
                            key={item.case_id}
                            href={`/guests/detail?guest_id=${encodeURIComponent(
                              item.guest_id
                            )}`}
                            className="block px-5 py-4 transition hover:bg-zinc-900/80"
                          >
                            <div className="flex flex-wrap items-center gap-2">
                              <p className="text-sm font-semibold text-zinc-200">
                                {titleCase(
                                  item.category
                                )}{" "}
                                Case
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

                              {item.priority && (
                                <span
                                  className={[
                                    "rounded-full border px-2 py-0.5 text-[9px] font-medium",
                                    statusClasses(
                                      item.priority
                                    ),
                                  ].join(" ")}
                                >
                                  {item.priority}
                                </span>
                              )}
                            </div>

                            <p className="mt-2 text-xs leading-5 text-zinc-500">
                              {item.summary ??
                                "Operational Case"}
                            </p>

                            <p className="mt-2 text-[10px] text-zinc-700">
                              {item.first_name}{" "}
                              {item.last_name}
                              {" · "}
                              {item.property_title}
                              {" · "}
                              {item.case_id}
                            </p>
                          </Link>
                        )
                      )}
                    </div>
                  </section>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
