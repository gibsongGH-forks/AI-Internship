"use client";

import { useEffect, useRef, useState } from "react";
import { Button, Callout, DemoHeader, Mono, Panel } from "../ui";

type Phase = "idle" | "running" | "crashed" | "done";

type Checkpoint = {
  step: number;
  note: string;
};

const STEPS = [
  "Load lead list",
  "Enrich company size",
  "Draft outreach",
  "Queue for review",
];

export function Demo6Checkpoint() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [step, setStep] = useState(0);
  const [inNodeProgress, setInNodeProgress] = useState(0);
  const [checkpoint, setCheckpoint] = useState<Checkpoint | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const timer = useRef<number | null>(null);

  function push(line: string) {
    setLog((L) => [...L, line]);
  }

  function clearTimer() {
    if (timer.current != null) {
      window.clearInterval(timer.current);
      timer.current = null;
    }
  }

  useEffect(() => () => clearTimer(), []);

  function runFrom(startStep: number, resume: boolean) {
    clearTimer();
    setPhase("running");
    setStep(startStep);
    setInNodeProgress(0);
    push(
      resume
        ? `Resumed from checkpoint at step ${startStep}. Progress inside the node starts at 0% again.`
        : `Started at step ${startStep}`,
    );

    let localStep = startStep;
    let localProgress = 0;

    timer.current = window.setInterval(() => {
      localProgress += 20;
      setInNodeProgress(localProgress);

      if (localProgress >= 100) {
        const finished = localStep;
        push(`Checkpoint saved after: ${STEPS[finished]}`);
        setCheckpoint({ step: finished + 1, note: STEPS[finished] });
        localStep += 1;
        localProgress = 0;
        setStep(localStep);
        setInNodeProgress(0);

        if (localStep >= STEPS.length) {
          clearTimer();
          setPhase("done");
          push("Pipeline complete.");
        }
      }
    }, 800);
  }

  function crash() {
    if (phase !== "running") return;
    clearTimer();
    setPhase("crashed");
    push(
      `Crashed during "${STEPS[step]}" at ${inNodeProgress}% progress. Only completed steps were saved.`,
    );
  }

  function reset() {
    clearTimer();
    setPhase("idle");
    setStep(0);
    setInNodeProgress(0);
    setCheckpoint(null);
    setLog([]);
  }

  return (
    <div>
      <DemoHeader
        kicker="Demo 6"
        title="Kill mid-run, resume from checkpoint"
        blurb="Checkpoints usually save between steps. If the process dies mid-step, unfinished work in that step is lost."
      />

      <div className="mb-4 flex flex-wrap gap-2">
        <Button
          onClick={() => runFrom(0, false)}
          disabled={phase === "running"}
        >
          Start pipeline
        </Button>
        <Button
          variant="danger"
          onClick={crash}
          disabled={phase !== "running"}
        >
          Kill mid-run
        </Button>
        <Button
          variant="secondary"
          onClick={() => runFrom(checkpoint?.step ?? 0, true)}
          disabled={phase !== "crashed"}
        >
          Resume
        </Button>
        <Button variant="ghost" onClick={reset}>
          Reset
        </Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Pipeline nodes">
          <ol className="space-y-2">
            {STEPS.map((label, i) => {
              const done = step > i || phase === "done";
              const active = phase === "running" && step === i;
              return (
                <li
                  key={label}
                  className={`rounded-lg border px-3 py-2 text-sm ${
                    active
                      ? "border-blue-300 bg-blue-50"
                      : done
                        ? "border-emerald-200 bg-emerald-50/50"
                        : "border-slate-200 bg-white"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-slate-800">
                      {i + 1}. {label}
                    </span>
                    <span className="text-xs text-slate-500">
                      {done ? "done" : active ? "running" : "pending"}
                    </span>
                  </div>
                  {active ? (
                    <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white">
                      <div
                        className="h-full bg-blue-600 transition-all"
                        style={{ width: `${inNodeProgress}%` }}
                      />
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ol>
        </Panel>

        <Panel title="Checkpoint + event log" tone="accent">
          <p className="mb-3 text-sm text-slate-700">
            Last durable checkpoint:{" "}
            {checkpoint ? (
              <Mono>{`next_step=${checkpoint.step}`}</Mono>
            ) : (
              <span className="text-slate-500">none</span>
            )}
          </p>
          <ul className="mono max-h-64 space-y-1.5 overflow-auto text-[11px] leading-relaxed text-slate-700">
            {log.length === 0 ? (
              <li className="text-slate-400">No events yet.</li>
            ) : (
              log.map((line, i) => <li key={i}>• {line}</li>)
            )}
          </ul>
        </Panel>
      </div>

      <div className="mt-4">
        <Callout tone={phase === "crashed" ? "warn" : "accent"}>
          {phase === "crashed"
            ? "Resume continues from the last completed step. Progress inside the crashed step starts over from 0%."
            : "Start the pipeline, kill it while a step is running, then resume. Notice which work survives."}
        </Callout>
      </div>
    </div>
  );
}
