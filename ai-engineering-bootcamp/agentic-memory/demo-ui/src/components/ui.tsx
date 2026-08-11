import { ReactNode } from "react";

export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">
      {children}
    </p>
  );
}

export function DemoHeader({
  kicker,
  title,
  blurb,
}: {
  kicker: string;
  title: string;
  blurb: string;
}) {
  return (
    <header className="mb-8 max-w-2xl">
      <SectionLabel>{kicker}</SectionLabel>
      <h1 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
        {title}
      </h1>
      <p className="mt-2 text-[15px] leading-relaxed text-slate-600">{blurb}</p>
    </header>
  );
}

export function Panel({
  title,
  children,
  tone = "default",
}: {
  title?: string;
  children: ReactNode;
  tone?: "default" | "accent" | "warn" | "ok" | "danger";
}) {
  const tones = {
    default: "border-slate-200 bg-white",
    accent: "border-blue-200 bg-blue-50/60",
    warn: "border-amber-200 bg-amber-50/70",
    ok: "border-emerald-200 bg-emerald-50/60",
    danger: "border-red-200 bg-red-50/70",
  };
  return (
    <div className={`rounded-xl border p-4 sm:p-5 ${tones[tone]}`}>
      {title ? (
        <h3 className="mb-3 text-sm font-semibold text-slate-900">{title}</h3>
      ) : null}
      {children}
    </div>
  );
}

export function Button({
  children,
  onClick,
  variant = "primary",
  disabled,
  type = "button",
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "danger" | "ghost";
  disabled?: boolean;
  type?: "button" | "submit";
}) {
  const styles = {
    primary:
      "bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-300",
    secondary:
      "bg-white text-slate-800 border border-slate-200 hover:bg-slate-50 disabled:opacity-50",
    danger: "bg-red-600 text-white hover:bg-red-700 disabled:bg-red-300",
    ghost: "bg-transparent text-slate-600 hover:bg-slate-100 disabled:opacity-50",
  };
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`inline-flex items-center justify-center rounded-lg px-3.5 py-2 text-sm font-medium transition ${styles[variant]}`}
    >
      {children}
    </button>
  );
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={`w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none ring-blue-500/30 placeholder:text-slate-400 focus:ring-2 ${props.className ?? ""}`}
    />
  );
}

export function Callout({
  children,
  tone = "accent",
}: {
  children: ReactNode;
  tone?: "accent" | "warn" | "ok" | "danger";
}) {
  const tones = {
    accent: "border-blue-200 bg-blue-50 text-blue-950",
    warn: "border-amber-200 bg-amber-50 text-amber-950",
    ok: "border-emerald-200 bg-emerald-50 text-emerald-950",
    danger: "border-red-200 bg-red-50 text-red-950",
  };
  return (
    <div className={`rounded-lg border px-3.5 py-3 text-sm leading-relaxed ${tones[tone]}`}>
      {children}
    </div>
  );
}

export function Mono({ children }: { children: ReactNode }) {
  return (
    <code className="mono rounded bg-slate-100 px-1.5 py-0.5 text-[12px] text-slate-800">
      {children}
    </code>
  );
}
