"use client";

import { useMemo, useState } from "react";
import { Callout, DemoHeader, Panel } from "../ui";

const LIMIT = 128_000;

export function Demo1Context() {
  const [messages, setMessages] = useState(24);
  const [tools, setTools] = useState(8);
  const [memory, setMemory] = useState(12);

  const tokens = useMemo(() => {
    const chat = messages * 420;
    const tool = tools * 1800;
    const mem = memory * 350;
    const system = 2400;
    const total = chat + tool + mem + system;
    return { chat, tool, mem, system, total, pct: Math.min(100, (total / LIMIT) * 100) };
  }, [messages, tools, memory]);

  return (
    <div>
      <DemoHeader
        kicker="Demo 1"
        title="Context is a budget"
        blurb="Every turn costs tokens. Chat history, tool results, and memory files all share one context window."
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="What you load">
          <Slider label="Chat turns" value={messages} min={4} max={80} onChange={setMessages} />
          <Slider label="Tool results" value={tools} min={0} max={20} onChange={setTools} />
          <Slider label="Memory files" value={memory} min={0} max={40} onChange={setMemory} />
        </Panel>

        <Panel title="Window usage">
          <div className="mb-3 flex items-end justify-between">
            <div>
              <p className="text-3xl font-semibold tabular-nums text-slate-900">
                {tokens.total.toLocaleString()}
              </p>
              <p className="text-sm text-slate-500">
                of {LIMIT.toLocaleString()} tokens (est.)
              </p>
            </div>
            <p className="text-sm font-medium tabular-nums text-slate-700">
              {tokens.pct.toFixed(0)}%
            </p>
          </div>
          <div className="mb-4 h-3 overflow-hidden rounded-full bg-slate-100">
            <div
              className={`h-full rounded-full transition-all ${
                tokens.pct > 90
                  ? "bg-red-500"
                  : tokens.pct > 70
                    ? "bg-amber-500"
                    : "bg-blue-600"
              }`}
              style={{ width: `${tokens.pct}%` }}
            />
          </div>
          <StackRow label="System" value={tokens.system} color="bg-slate-400" />
          <StackRow label="Chat" value={tokens.chat} color="bg-blue-500" />
          <StackRow label="Tools" value={tokens.tool} color="bg-indigo-400" />
          <StackRow label="Memory" value={tokens.mem} color="bg-sky-400" />
        </Panel>
      </div>

      <div className="mt-4">
        <Callout tone={tokens.pct > 85 ? "warn" : "accent"}>
          {tokens.pct > 85
            ? "You are near the limit. Compact the chat or load only the memory you need."
            : "Memory is not free. Loading everything into context can crowd out the actual task."}
        </Callout>
      </div>
    </div>
  );
}

function Slider({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  onChange: (n: number) => void;
}) {
  return (
    <label className="mb-4 block last:mb-0">
      <div className="mb-1.5 flex justify-between text-sm">
        <span className="text-slate-700">{label}</span>
        <span className="mono tabular-nums text-slate-500">{value}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-blue-600"
      />
    </label>
  );
}

function StackRow({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="mb-2 flex items-center gap-3 text-sm last:mb-0">
      <span className={`h-2.5 w-2.5 rounded-full ${color}`} />
      <span className="w-16 text-slate-600">{label}</span>
      <span className="mono tabular-nums text-slate-800">
        {value.toLocaleString()}
      </span>
    </div>
  );
}
