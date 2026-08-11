export const SAMPLE_NOTES: Record<string, string> = {
  "acme_people.md": `# Acme Corp roster

[[Alice Chen]] works_at [[Acme Corp]]. Role: VP Engineering.
[[Bob Diaz]] works_at [[Acme Corp]]. Role: Staff Engineer.
[[Carol Ng]] works_at [[Acme Corp]]. Role: Product Manager.

[[Alice Chen]] reports_to nobody at Acme (executive).
[[Bob Diaz]] reports_to [[Alice Chen]].
[[Carol Ng]] reports_to [[Alice Chen]].

Meeting notes mention Acme often when discussing partnership pricing.
`,
  "alice_meetings.md": `# Notes about Alice

Last 1:1 with [[Alice Chen]] on 22 April: discussed Q2 hiring freeze and preference for Friday ship windows.

No updates about Alice since 22 April. She may have replied via email outside this notes corpus.
`,
  "acme_pricing.md": `# Acme partnership pricing

Acme Corp is evaluating a multi-seat plan. Pages that talk about Acme pricing often mention discount tiers and seat minimums.

This note talks about Acme a lot but does not list who works there.
`,
};
