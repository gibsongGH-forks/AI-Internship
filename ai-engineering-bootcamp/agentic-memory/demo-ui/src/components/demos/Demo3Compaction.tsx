"use client";

import { useState } from "react";
import { Button, Callout, DemoHeader, Mono, Panel } from "../ui";

const RULE = "Always answer pricing questions in EUR, never USD.";

export function Demo3Compaction() {
  const [compacted, setCompacted] = useState(false);
  const [inFile, setInFile] = useState(true);

  const chatHasRule = !compacted;

  return (
    <div>
      <DemoHeader
        kicker="Demo 3"
        title="Put important rules in a file"
        blurb="When a long chat is compacted, early instructions can disappear. The same rule written to MEMORY.md stays available."
      />

      <div className="mb-4 flex flex-wrap gap-2">
        <Button
          variant={compacted ? "danger" : "primary"}
          onClick={() => setCompacted((v) => !v)}
        >
          {compacted ? "Undo compaction" : "Compact the chat"}
        </Button>
        <Button variant="secondary" onClick={() => setInFile((v) => !v)}>
          {inFile ? "Clear MEMORY.md" : "Save rule to MEMORY.md"}
        </Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Chat transcript" tone={chatHasRule ? "default" : "warn"}>
          {chatHasRule ? (
            <div className="space-y-3 text-sm">
              <Bubble who="You">For this project: {RULE}</Bubble>
              <Bubble who="Agent">Got it. I will use EUR for pricing.</Bubble>
              <Bubble who="You">What is the Acme seat price?</Bubble>
            </div>
          ) : (
            <div className="space-y-3 text-sm">
              <p className="rounded-lg bg-amber-100/80 px-3 py-2 text-amber-950">
                [compacted] Earlier discussion about project preferences summarised away.
              </p>
              <Bubble who="You">What is the Acme seat price?</Bubble>
              <Bubble who="Agent">
                Looking at notes… I will quote in USD (default habit).
              </Bubble>
            </div>
          )}
        </Panel>

        <Panel title="MEMORY.md" tone={inFile ? "ok" : "default"}>
          {inFile ? (
            <pre className="mono whitespace-pre-wrap text-[12px] leading-relaxed text-slate-800">
              {`# Project rules\n\n- ${RULE}`}
            </pre>
          ) : (
            <p className="text-sm text-slate-500">(empty)</p>
          )}
          <p className="mt-3 text-sm text-slate-600">
            After compaction, the agent can still follow this if the file is
            loaded into context.
          </p>
        </Panel>
      </div>

      <div className="mt-4">
        <Callout tone={!chatHasRule && inFile ? "ok" : !chatHasRule ? "warn" : "accent"}>
          {!chatHasRule && inFile ? (
            <>
              The chat forgot the EUR rule. <Mono>MEMORY.md</Mono> still has it.
              Store critical preferences outside the transcript.
            </>
          ) : !chatHasRule ? (
            <>
              The rule is gone from both chat and file, so the agent falls back
              to a default (USD here).
            </>
          ) : (
            <>
              Compact the chat to see the spoken rule disappear. Keep{" "}
              <Mono>MEMORY.md</Mono> on to see why file-based rules survive.
            </>
          )}
        </Callout>
      </div>
    </div>
  );
}

function Bubble({ who, children }: { who: string; children: React.ReactNode }) {
  const you = who === "You";
  return (
    <div
      className={`rounded-lg px-3 py-2 ${
        you ? "bg-slate-100 text-slate-800" : "bg-blue-50 text-slate-800"
      }`}
    >
      <p className="mb-0.5 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
        {who}
      </p>
      <p>{children}</p>
    </div>
  );
}
