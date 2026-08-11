"use client";

import { useMemo, useState } from "react";
import { vectorSearch } from "@/lib/memory";
import { SAMPLE_NOTES } from "@/lib/sampleNotes";
import { Button, Callout, DemoHeader, Input, Mono, Panel } from "../ui";

export function Demo4SearchSynth() {
  const [q, setQ] = useState("updates about Alice");
  const [mode, setMode] = useState<"idle" | "search" | "synth">("idle");

  const hits = useMemo(() => vectorSearch(SAMPLE_NOTES, q, 2), [q]);

  const synthesis =
    "Alice Chen (VP Eng, Acme) had a 1:1 on 22 April about hiring freeze and Friday ship windows. Corpus has no newer Alice updates after that date.";

  return (
    <div>
      <DemoHeader
        kicker="Demo 4"
        title="Search is not synthesis"
        blurb="Search finds relevant notes. Synthesis turns those notes into an answer, including what is still unknown."
      />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <Input value={q} onChange={(e) => setQ(e.target.value)} />
        <div className="flex gap-2">
          <Button
            variant="secondary"
            onClick={() => setMode("search")}
          >
            Search only
          </Button>
          <Button onClick={() => setMode("synth")}>Search + synthesise</Button>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Retrieved notes">
          {mode === "idle" ? (
            <p className="text-sm text-slate-500">Run a mode to see results.</p>
          ) : (
            <ul className="space-y-3">
              {hits.map((h) => (
                <li key={h.name}>
                  <Mono>{h.name}</Mono>
                  <p className="mt-1 text-sm leading-relaxed text-slate-600">
                    {SAMPLE_NOTES[h.name].trim().slice(0, 220)}…
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel
          title="Answer"
          tone={mode === "synth" ? "ok" : mode === "search" ? "warn" : "default"}
        >
          {mode === "idle" && (
            <p className="text-sm text-slate-500">No answer yet.</p>
          )}
          {mode === "search" && (
            <p className="text-sm text-slate-700">
              Top matching notes only. You still need a step that answers the
              question.
            </p>
          )}
          {mode === "synth" && (
            <p className="text-sm leading-relaxed text-slate-800">{synthesis}</p>
          )}
        </Panel>
      </div>

      <div className="mt-4">
        <Callout tone={mode === "search" ? "warn" : "accent"}>
          Good memory systems do both: find the right evidence, then write a
          clear answer that includes dates and gaps.
        </Callout>
      </div>
    </div>
  );
}
