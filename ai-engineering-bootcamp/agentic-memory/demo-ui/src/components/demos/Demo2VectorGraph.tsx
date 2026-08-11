"use client";

import { useMemo, useState } from "react";
import {
  buildGraph,
  graphQuery,
  vectorSearch,
} from "@/lib/memory";
import { SAMPLE_NOTES } from "@/lib/sampleNotes";
import { Button, Callout, DemoHeader, Input, Mono, Panel } from "../ui";

export function Demo2VectorGraph() {
  const [query, setQuery] = useState("Who works at Acme?");
  const [entity, setEntity] = useState("Acme Corp");
  const [ran, setRan] = useState(false);

  const edges = useMemo(() => buildGraph(SAMPLE_NOTES), []);
  const vectorHits = useMemo(
    () => (ran ? vectorSearch(SAMPLE_NOTES, query, 3) : []),
    [query, ran],
  );
  const graphHits = useMemo(
    () => (ran ? graphQuery(edges, entity, "works_at") : []),
    [edges, entity, ran],
  );

  return (
    <div>
      <DemoHeader
        kicker="Demo 2"
        title="Vector search vs graph lookup"
        blurb="Same notes corpus, two retrieval modes. Vector ranks similar text. Graph returns typed links like works_at from [[wikilinks]]."
      />

      <div className="mb-4 grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Vector query"
        />
        <Input
          value={entity}
          onChange={(e) => setEntity(e.target.value)}
          placeholder="Graph entity"
        />
        <Button onClick={() => setRan(true)}>Run both</Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Vector (bag-of-words cosine)">
          {!ran ? (
            <p className="text-sm text-slate-500">Run to see ranked notes.</p>
          ) : (
            <ul className="space-y-3">
              {vectorHits.map((h) => (
                <li key={h.name} className="border-b border-slate-100 pb-3 last:border-0 last:pb-0">
                  <div className="flex items-baseline justify-between gap-2">
                    <Mono>{h.name}</Mono>
                    <span className="mono text-xs text-slate-500">
                      {h.score.toFixed(3)}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-slate-600">{h.preview}</p>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel title='Graph (works_at edges)' tone="accent">
          {!ran ? (
            <p className="text-sm text-slate-500">Run to see exact edges.</p>
          ) : graphHits.length === 0 ? (
            <p className="text-sm text-slate-600">No matching edges.</p>
          ) : (
            <ul className="space-y-2">
              {graphHits.map((e, i) => (
                <li key={i} className="mono text-sm text-slate-800">
                  {e.src} <span className="text-blue-600">→ {e.rel} →</span> {e.dst}
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>

      <div className="mt-4">
        <Callout>
          Vector can rank a pricing note highly just because it mentions Acme a
          lot. Graph returns the people who <Mono>works_at</Mono> Acme. Use the
          store that matches the question.
        </Callout>
      </div>

      <details className="mt-4 rounded-xl border border-slate-200 bg-white p-4">
        <summary className="cursor-pointer text-sm font-medium text-slate-800">
          Sample notes corpus
        </summary>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          {Object.entries(SAMPLE_NOTES).map(([name, text]) => (
            <pre
              key={name}
              className="mono max-h-48 overflow-auto rounded-lg bg-slate-50 p-3 text-[11px] leading-relaxed text-slate-700"
            >
              {`# ${name}\n\n${text.trim()}`}
            </pre>
          ))}
        </div>
      </details>
    </div>
  );
}
