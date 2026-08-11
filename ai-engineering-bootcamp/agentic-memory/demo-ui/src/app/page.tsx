"use client";

import { useState } from "react";
import { Demo1Context } from "@/components/demos/Demo1Context";
import { Demo2VectorGraph } from "@/components/demos/Demo2VectorGraph";
import { Demo3Compaction } from "@/components/demos/Demo3Compaction";
import { Demo4SearchSynth } from "@/components/demos/Demo4SearchSynth";
import { Demo5SelfEdit } from "@/components/demos/Demo5SelfEdit";
import { Demo6Checkpoint } from "@/components/demos/Demo6Checkpoint";
import { Demo7Poison } from "@/components/demos/Demo7Poison";

const DEMOS = [
  { id: "1", label: "Context budget", Component: Demo1Context },
  { id: "2", label: "Vector vs graph", Component: Demo2VectorGraph },
  { id: "3", label: "Compaction rules", Component: Demo3Compaction },
  { id: "4", label: "Search vs synthesis", Component: Demo4SearchSynth },
  { id: "5", label: "Self-editing memory", Component: Demo5SelfEdit },
  { id: "6", label: "Kill mid-run", Component: Demo6Checkpoint },
  { id: "7", label: "Memory poisoning", Component: Demo7Poison },
] as const;

export default function Home() {
  const [active, setActive] = useState<(typeof DEMOS)[number]["id"]>("1");
  const current = DEMOS.find((d) => d.id === active) ?? DEMOS[0];
  const Active = current.Component;

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[260px_1fr]">
      <aside className="border-b border-slate-200 bg-white lg:sticky lg:top-0 lg:h-screen lg:border-b-0 lg:border-r">
        <div className="px-5 pb-4 pt-6">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-600">
            AI Eng · Week 5
          </p>
          <h1 className="mt-1 text-lg font-semibold tracking-tight text-slate-900">
            Agentic Memory Lab
          </h1>
          <p className="mt-1.5 text-[13px] leading-snug text-slate-500">
            Seven demos you can run yourself. No API key needed.
          </p>
        </div>

        <nav className="px-3 pb-6" aria-label="Demos">
          <ul className="space-y-0.5">
            {DEMOS.map((d, i) => {
              const on = d.id === active;
              return (
                <li key={d.id}>
                  <button
                    type="button"
                    onClick={() => setActive(d.id)}
                    className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition ${
                      on
                        ? "bg-blue-50 font-medium text-blue-900"
                        : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                    }`}
                  >
                    <span
                      className={`mono flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-[11px] ${
                        on
                          ? "bg-blue-600 text-white"
                          : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      {i + 1}
                    </span>
                    {d.label}
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="hidden border-t border-slate-100 px-5 py-4 text-xs leading-relaxed text-slate-500 lg:block">
          Work through each demo in order. Optional notebook code lives in{" "}
          <span className="mono text-slate-700">agentic-memory/</span>.
        </div>
      </aside>

      <main className="px-5 py-8 sm:px-8 lg:px-12 lg:py-10">
        <div className="mx-auto max-w-4xl">
          <Active />
        </div>
      </main>
    </div>
  );
}
