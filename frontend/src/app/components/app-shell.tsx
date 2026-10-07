"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

type NavItem = {
  href: string;
  label: string;
  description: string;
  icon: ReactNode;
  exact?: boolean;
};

function GridIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" className="h-4 w-4" aria-hidden="true">
      <rect x="3.5" y="3.5" width="7" height="7" rx="1.5" />
      <rect x="13.5" y="3.5" width="7" height="7" rx="1.5" />
      <rect x="3.5" y="13.5" width="7" height="7" rx="1.5" />
      <rect x="13.5" y="13.5" width="7" height="7" rx="1.5" />
    </svg>
  );
}

function ChatIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" className="h-4 w-4" aria-hidden="true">
      <path d="M7 18.5 3.5 20l1.1-3.5A8.5 8.5 0 1 1 7 18.5Z" />
      <path d="M8 10.5h8M8 14h5" />
    </svg>
  );
}

function GuestsIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" className="h-4 w-4" aria-hidden="true">
      <circle cx="9" cy="8" r="3.2" />
      <path d="M3.5 19c.5-3.7 2.4-5.5 5.5-5.5s5 1.8 5.5 5.5" />
      <path d="M15.5 5.5a3 3 0 0 1 0 5.7M16 13.7c2.6.4 4 2.1 4.5 5.3" />
    </svg>
  );
}

function OperationsIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" className="h-4 w-4" aria-hidden="true">
      <path d="M12 3.5 20 7.7v8.6L12 20.5 4 16.3V7.7L12 3.5Z" />
      <path d="m4.5 8 7.5 4 7.5-4M12 12v8" />
    </svg>
  );
}

const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Overview", description: "Operational snapshot", icon: <GridIcon /> },
  { href: "/", label: "Guest Ops", description: "AI guest workspace", icon: <ChatIcon />, exact: true },
  { href: "/guests", label: "Guests", description: "Guest directory", icon: <GuestsIcon /> },
  { href: "/operations", label: "Operations", description: "Human handoffs", icon: <OperationsIcon /> },
];

function isActive(pathname: string, item: NavItem) {
  if (item.exact) return pathname === item.href;
  return pathname === item.href || pathname.startsWith(`${item.href}/`);
}

function Navigation({
  pathname,
  mobile = false,
}: {
  pathname: string;
  mobile?: boolean;
}) {
  if (mobile) {
    return (
      <nav className="flex gap-1 overflow-x-auto px-4 pb-3" aria-label="StayOps navigation">
        {NAV_ITEMS.map((item) => {
          const active = isActive(pathname, item);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={[
                "flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium transition",
                active
                  ? "bg-white text-zinc-950"
                  : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100",
              ].join(" ")}
            >
              {item.icon}
              {item.label}
            </Link>
          );
        })}
      </nav>
    );
  }

  return (
    <nav className="mt-7 space-y-1" aria-label="StayOps navigation">
      {NAV_ITEMS.map((item) => {
        const active = isActive(pathname, item);

        return (
          <Link
            key={item.href}
            href={item.href}
            className={[
              "group flex items-center gap-3 rounded-xl px-3 py-3 transition",
              active
                ? "bg-zinc-100 text-zinc-950"
                : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100",
            ].join(" ")}
          >
            <span
              className={[
                "flex h-8 w-8 items-center justify-center rounded-lg border transition",
                active
                  ? "border-zinc-300 bg-white text-zinc-950"
                  : "border-zinc-800 bg-zinc-950 text-zinc-500 group-hover:border-zinc-700 group-hover:text-zinc-300",
              ].join(" ")}
            >
              {item.icon}
            </span>

            <span className="min-w-0">
              <span className="block text-sm font-medium">{item.label}</span>
              <span className={["mt-0.5 block text-[11px]", active ? "text-zinc-500" : "text-zinc-600"].join(" ")}>
                {item.description}
              </span>
            </span>
          </Link>
        );
      })}
    </nav>
  );
}

function Brand() {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-sm font-bold tracking-tight text-zinc-950 shadow-sm">
        SO
      </div>

      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <p className="font-semibold tracking-tight text-zinc-100">StayOps</p>
          <span className="rounded-full border border-violet-500/20 bg-violet-500/10 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-[0.14em] text-violet-300">
            Demo
          </span>
        </div>
        <p className="mt-0.5 text-[11px] text-zinc-600">AI guest operations</p>
      </div>
    </div>
  );
}

export default function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col border-r border-zinc-800/80 bg-[#0c0c0f] px-4 py-5 lg:flex">
        <div className="px-2">
          <Brand />
        </div>

        <Navigation pathname={pathname} />

        <div className="mt-auto px-2">
          <div className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-3">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.55)]" />
              <span className="text-xs font-medium text-zinc-300">System online</span>
            </div>
            <p className="mt-2 text-[11px] leading-relaxed text-zinc-600">
              Agent runtime and human operations are connected.
            </p>
          </div>

          <p className="mt-3 px-1 text-[10px] uppercase tracking-[0.16em] text-zinc-700">
            V5 product demo
          </p>
        </div>
      </aside>

      <div className="min-h-screen lg:pl-64">
        <header className="sticky top-0 z-30 border-b border-zinc-800/80 bg-[#0c0c0f]/95 backdrop-blur lg:hidden">
          <div className="flex items-center justify-between px-4 py-3">
            <Brand />
            <div className="flex items-center gap-2 text-[11px] text-zinc-500">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              Online
            </div>
          </div>

          <Navigation pathname={pathname} mobile />
        </header>

        <div className="min-h-screen">{children}</div>
      </div>
    </div>
  );
}
