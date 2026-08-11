"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  MEMORY_KEY,
  HumanMemory,
  clearMemory,
  loadMemory,
  saveMemory,
} from "@/lib/memory";
import { Button, Callout, DemoHeader, Input, Mono, Panel } from "../ui";

export function Demo5SelfEdit() {
  const [store, setStore] = useState<HumanMemory>({});
  const [key, setKey] = useState("preferred_currency");
  const [value, setValue] = useState("EUR");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setStore(loadMemory());
    setReady(true);
  }, []);

  function persist(next: HumanMemory) {
    setStore(next);
    saveMemory(next);
  }

  function onSave(e: FormEvent) {
    e.preventDefault();
    if (!key.trim()) return;
    persist({ ...store, [key.trim()]: value });
  }

  function onClear() {
    clearMemory();
    setStore({});
  }

  return (
    <div>
      <DemoHeader
        kicker="Demo 5"
        title="Self-editing memory"
        blurb="Write a fact to durable storage, then read it back as if this were a new session. This lab uses browser localStorage."
      />

      <form onSubmit={onSave} className="mb-4 grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
        <Input
          value={key}
          onChange={(e) => setKey(e.target.value)}
          placeholder="key"
        />
        <Input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="value"
        />
        <Button type="submit">Write</Button>
      </form>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Memory store">
          {!ready ? (
            <p className="text-sm text-slate-500">Loading…</p>
          ) : Object.keys(store).length === 0 ? (
            <p className="text-sm text-slate-500">Empty. Write a fact above.</p>
          ) : (
            <ul className="space-y-2">
              {Object.entries(store).map(([k, v]) => (
                <li
                  key={k}
                  className="flex items-start justify-between gap-3 rounded-lg bg-slate-50 px-3 py-2"
                >
                  <div>
                    <Mono>{k}</Mono>
                    <p className="mt-1 text-sm text-slate-700">{v}</p>
                  </div>
                  <Button
                    variant="ghost"
                    onClick={() => {
                      const next = { ...store };
                      delete next[k];
                      persist(next);
                    }}
                  >
                    Delete
                  </Button>
                </li>
              ))}
            </ul>
          )}
          <div className="mt-3">
            <Button variant="secondary" onClick={onClear}>
              Clear store
            </Button>
          </div>
        </Panel>

        <Panel title="What the agent reads next" tone="accent">
          <p className="text-sm leading-relaxed text-slate-700">
            On the next turn, memory can be loaded into the prompt like this:
          </p>
          <pre className="mono mt-3 whitespace-pre-wrap rounded-lg bg-white p-3 text-[12px] leading-relaxed text-slate-800">
            {Object.keys(store).length === 0
              ? "# memory\n(none)"
              : `# memory\n${Object.entries(store)
                  .map(([k, v]) => `- ${k}: ${v}`)
                  .join("\n")}`}
          </pre>
          <p className="mt-3 text-xs text-slate-500">
            Stored in this browser as <Mono>{MEMORY_KEY}</Mono>
          </p>
        </Panel>
      </div>

      <div className="mt-4">
        <Callout>
          Refresh the page and the facts are still there. Real agent memory
          should survive a new session, not only a longer chat.
        </Callout>
      </div>
    </div>
  );
}
