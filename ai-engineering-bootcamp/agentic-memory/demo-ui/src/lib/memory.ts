export type SearchHit = { name: string; score: number; preview: string };
export type GraphEdge = { src: string; rel: string; dst: string };

const WIKILINK = /\[\[([^\]]+)\]\]/g;
const EDGE = /\[\[([^\]]+)\]\]\s+(works_at|reports_to)\s+\[\[([^\]]+)\]\]/gi;

function tokenize(text: string): string[] {
  return text.toLowerCase().match(/[a-z0-9]+/g) ?? [];
}

function bag(text: string, vocab: string[]): number[] {
  const counts = new Map<string, number>();
  for (const t of tokenize(text)) counts.set(t, (counts.get(t) ?? 0) + 1);
  return vocab.map((t) => counts.get(t) ?? 0);
}

function cosine(a: number[], b: number[]): number {
  let dot = 0;
  let na = 0;
  let nb = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  if (!na || !nb) return 0;
  return dot / (Math.sqrt(na) * Math.sqrt(nb));
}

export function vectorSearch(
  docs: Record<string, string>,
  query: string,
  k = 3,
): SearchHit[] {
  const vocab = Array.from(
    new Set(Object.values(docs).flatMap((t) => tokenize(t))),
  ).sort();
  const q = bag(query, vocab);
  return Object.entries(docs)
    .map(([name, text]) => ({
      name,
      score: cosine(q, bag(text, vocab)),
      preview: text.trim().split("\n")[0] ?? "",
    }))
    .sort((a, b) => b.score - a.score)
    .slice(0, k);
}

export function buildGraph(docs: Record<string, string>): GraphEdge[] {
  const edges: GraphEdge[] = [];
  for (const text of Object.values(docs)) {
    for (const m of text.matchAll(EDGE)) {
      edges.push({
        src: m[1].trim(),
        rel: m[2].toLowerCase(),
        dst: m[3].trim(),
      });
    }
  }
  return edges;
}

export function graphQuery(
  edges: GraphEdge[],
  entity: string,
  rel?: string,
): GraphEdge[] {
  const e = entity.toLowerCase();
  return edges.filter((edge) => {
    if (rel && edge.rel !== rel.toLowerCase()) return false;
    return edge.src.toLowerCase() === e || edge.dst.toLowerCase() === e;
  });
}

export type HumanMemory = Record<string, string>;

const MEMORY_KEY = "tai-agentic-memory-human";
const POISON_KEY = "tai-agentic-memory-poison";

export function loadMemory(key = MEMORY_KEY): HumanMemory {
  if (typeof window === "undefined") return {};
  try {
    return JSON.parse(localStorage.getItem(key) ?? "{}") as HumanMemory;
  } catch {
    return {};
  }
}

export function saveMemory(data: HumanMemory, key = MEMORY_KEY) {
  localStorage.setItem(key, JSON.stringify(data));
}

export function clearMemory(key = MEMORY_KEY) {
  localStorage.removeItem(key);
}

export { MEMORY_KEY, POISON_KEY, WIKILINK };
