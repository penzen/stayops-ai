"use client";

import Link from "next/link";
import {
  FormEvent,
  useEffect,
  useState,
} from "react";
import { useRouter } from "next/navigation";

type DemoProperty = {
  property_id: string;
  title: string;
  city: string | null;
  max_guests: number | null;
  base_price: number | null;
  cleaning_fee: number | null;
};

type CreatedStay = {
  booking_id: string;
  guest_id: string;
  property_id: string;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

export default function CreateDemoPage() {
  const router = useRouter();

  const [properties, setProperties] =
    useState<DemoProperty[]>([]);
  const [propertyId, setPropertyId] =
    useState("");
  const [firstName, setFirstName] =
    useState("");
  const [lastName, setLastName] =
    useState("");
  const [email, setEmail] =
    useState("");
  const [language, setLanguage] =
    useState("en");
  const [isLoading, setIsLoading] =
    useState(false);
  const [
    isPropertiesLoading,
    setIsPropertiesLoading,
  ] = useState(true);
  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    const controller =
      new AbortController();

    async function loadProperties() {
      try {
        const response = await fetch(
          `${API_URL}/demo/properties`,
          {
            signal: controller.signal,
          }
        );

        if (!response.ok) {
          throw new Error(
            `Properties request failed: ${response.status}`
          );
        }

        const data: DemoProperty[] =
          await response.json();

        setProperties(data);

        if (data.length > 0) {
          setPropertyId(
            (current) =>
              current ||
              data[0].property_id
          );
        }
      } catch (loadError) {
        if (
          loadError instanceof DOMException &&
          loadError.name === "AbortError"
        ) {
          return;
        }

        console.error(loadError);
        setError(
          "Unable to load demo properties."
        );
      } finally {
        setIsPropertiesLoading(false);
      }
    }

    void loadProperties();

    return () => {
      controller.abort();
    };
  }, []);

  async function submit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (isLoading) {
      return;
    }

    setError(null);
    setIsLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/demo/stays`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            first_name: firstName,
            last_name: lastName,
            email:
              email.trim() || null,
            guest_lang: language,
            property_id: propertyId,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ??
            "Unable to create demo stay."
        );
      }

      const createdStay =
        data as CreatedStay;

      window.localStorage.setItem(
        "stayops:selectedBookingId",
        createdStay.booking_id
      );

      router.push("/guest-ops");
    } catch (submitError) {
      console.error(submitError);

      setError(
        submitError instanceof Error
          ? submitError.message
          : "Unable to create demo stay."
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#09090b] text-zinc-100">
      <div className="mx-auto flex min-h-screen max-w-5xl flex-col px-6">
        <header className="flex items-center justify-between py-6">
          <Link
            href="/"
            className="flex items-center gap-3"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-sm font-bold text-zinc-950">
              SO
            </div>

            <div>
              <p className="font-semibold tracking-tight">
                StayOps
              </p>
              <p className="text-[11px] text-zinc-600">
                Interactive demo
              </p>
            </div>
          </Link>

          <Link
            href="/"
            className="text-xs font-medium text-zinc-500 transition hover:text-zinc-200"
          >
            Back to demo options
          </Link>
        </header>

        <div className="grid flex-1 items-center gap-10 py-12 lg:grid-cols-[0.85fr_1.15fr]">
          <section>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-300">
              Custom demo stay
            </p>

            <h1 className="mt-3 text-4xl font-semibold tracking-[-0.035em] text-white">
              Create a fictional guest.
            </h1>

            <p className="mt-4 max-w-md text-sm leading-6 text-zinc-500">
              Create a temporary guest and confirmed reservation,
              then use that stay with the same StayOps agent,
              Cases, tasks and human-handoff workflows.
            </p>

            <div className="mt-7 space-y-3 text-xs text-zinc-500">
              {[
                "No real personal information is required.",
                "Guest and booking IDs are generated by the backend.",
                "The stay is active immediately after creation.",
              ].map((item, index) => (
                <div
                  key={item}
                  className="flex items-start gap-3"
                >
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-zinc-800 bg-zinc-950 text-[10px] text-zinc-400">
                    {index + 1}
                  </span>
                  <span className="pt-1">
                    {item}
                  </span>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-[26px] border border-zinc-800 bg-zinc-950/60 p-2 shadow-2xl shadow-black/30">
            <form
              onSubmit={submit}
              className="rounded-[20px] border border-zinc-800 bg-[#0d0d10] p-6 sm:p-7"
            >
              <div>
                <h2 className="text-lg font-semibold tracking-tight">
                  Guest and reservation
                </h2>
                <p className="mt-1 text-xs text-zinc-600">
                  Everything here is fictional demo data.
                </p>
              </div>

              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                <label className="space-y-2">
                  <span className="text-xs font-medium text-zinc-400">
                    First name
                  </span>
                  <input
                    required
                    maxLength={80}
                    value={firstName}
                    onChange={(event) =>
                      setFirstName(
                        event.target.value
                      )
                    }
                    placeholder="Maya"
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3.5 py-3 text-sm outline-none transition placeholder:text-zinc-700 focus:border-blue-500/50"
                  />
                </label>

                <label className="space-y-2">
                  <span className="text-xs font-medium text-zinc-400">
                    Last name
                  </span>
                  <input
                    required
                    maxLength={80}
                    value={lastName}
                    onChange={(event) =>
                      setLastName(
                        event.target.value
                      )
                    }
                    placeholder="Patel"
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3.5 py-3 text-sm outline-none transition placeholder:text-zinc-700 focus:border-blue-500/50"
                  />
                </label>
              </div>

              <label className="mt-4 block space-y-2">
                <span className="text-xs font-medium text-zinc-400">
                  Email
                  <span className="ml-1 text-zinc-700">
                    optional
                  </span>
                </span>
                <input
                  type="email"
                  maxLength={255}
                  value={email}
                  onChange={(event) =>
                    setEmail(
                      event.target.value
                    )
                  }
                  placeholder="maya@example.com"
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3.5 py-3 text-sm outline-none transition placeholder:text-zinc-700 focus:border-blue-500/50"
                />
              </label>

              <div className="mt-4 grid gap-4 sm:grid-cols-[0.7fr_1.3fr]">
                <label className="space-y-2">
                  <span className="text-xs font-medium text-zinc-400">
                    Language
                  </span>
                  <select
                    value={language}
                    onChange={(event) =>
                      setLanguage(
                        event.target.value
                      )
                    }
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3.5 py-3 text-sm outline-none transition focus:border-blue-500/50"
                  >
                    <option value="en">
                      English
                    </option>
                    <option value="de">
                      Deutsch
                    </option>
                    <option value="fr">
                      Français
                    </option>
                  </select>
                </label>

                <label className="space-y-2">
                  <span className="text-xs font-medium text-zinc-400">
                    Property
                  </span>
                  <select
                    required
                    value={propertyId}
                    disabled={
                      isPropertiesLoading ||
                      properties.length === 0
                    }
                    onChange={(event) =>
                      setPropertyId(
                        event.target.value
                      )
                    }
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3.5 py-3 text-sm outline-none transition focus:border-blue-500/50 disabled:opacity-50"
                  >
                    {isPropertiesLoading && (
                      <option value="">
                        Loading properties...
                      </option>
                    )}

                    {!isPropertiesLoading &&
                      properties.length === 0 && (
                        <option value="">
                          No properties available
                        </option>
                      )}

                    {properties.map(
                      (property) => (
                        <option
                          key={
                            property.property_id
                          }
                          value={
                            property.property_id
                          }
                        >
                          {property.title}
                          {property.city
                            ? ` · ${property.city}`
                            : ""}
                        </option>
                      )
                    )}
                  </select>
                </label>
              </div>

              <div className="mt-5 rounded-xl border border-zinc-800 bg-zinc-950/60 px-4 py-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-zinc-600">
                    Stay status
                  </span>
                  <span className="font-medium text-emerald-300">
                    Active · 2 nights
                  </span>
                </div>
              </div>

              {error && (
                <div className="mt-4 rounded-xl border border-red-900/70 bg-red-950/20 px-4 py-3 text-xs text-red-300">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={
                  isLoading ||
                  isPropertiesLoading ||
                  !propertyId
                }
                className="mt-5 w-full rounded-xl bg-white px-5 py-3.5 text-sm font-semibold text-zinc-950 transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isLoading
                  ? "Creating demo stay..."
                  : "Create guest and enter StayOps"}
              </button>
            </form>
          </section>
        </div>
      </div>
    </main>
  );
}
