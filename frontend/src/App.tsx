import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import {
  Activity, AlertTriangle, BadgeCheck, Bot, Boxes, Clock, Layers,
  Library, MessageSquare, Network, Scale, Search, SlidersHorizontal,
} from 'lucide-react'
import { askStream } from './api'
import type { StreamStage } from './api'
import type { AskResponse } from './api'
import { Reveal } from './components/Reveal'

const NAV_LINKS = [
  { href: '#about', label: 'About' },
  { href: '#how-it-works', label: 'How it works' },
  { href: '#library', label: 'Library' },
  { href: '#evaluation', label: 'Evaluation' },
]

const SAMPLE_QUERIES = [
  'my employer is not paying my salary',
  'can police arrest me without a warrant',
  'a refund for a defective product',
  'my rights after a road accident',
  'someone forged my documents',
]

const TIPS = [
  'Every claim cites an Act and Section from real statute text.',
  'The answer only uses the sections retrieved below — nothing else.',
  'Retrieval blends keyword search with dense embeddings, then reranks.',
  'A relevance score sits next to each source, not just a citation.',
]

const KEY_STATS = [
  { value: '37', label: 'Statutes indexed' },
  { value: '12', label: 'Legal domains' },
  { value: '192', label: 'Labeled test cases' },
  { value: '100%', label: 'Hit@5 accuracy' },
]

const FEATURES = [
  {
    icon: Layers,
    tag: 'retrieval',
    title: 'Hybrid search',
    copy: 'Dense embeddings and BM25 lexical search run in parallel, so meaning and exact keywords both count.',
  },
  {
    icon: SlidersHorizontal,
    tag: 'reranking',
    title: 'Cross-encoder reranking',
    copy: 'A BAAI/bge-reranker-v2-m3 cross-encoder separates near-identical sections — the difference between BNS 101 and BNS 103.',
  },
  {
    icon: BadgeCheck,
    tag: 'generation',
    title: 'Grounded, cited answers',
    copy: 'Every claim in the answer ties back to an Act and Section pulled from the retrieved text — nothing invented.',
  },
]

const FLOW_STEPS = [
  { title: 'Query', copy: 'You ask a question in plain English — no legal terminology required.' },
  { title: 'Retrieval', copy: 'Dense (bge-m3) and lexical (BM25) search pull up to 80 candidate sections.' },
  { title: 'Reranking', copy: 'A cross-encoder rescores candidates; anchor boost promotes sections confirmed by multiple views.' },
  { title: 'Gemini', copy: 'The top 8 sections are passed as context to gemini-3.6-flash, which drafts a plain-language answer.' },
  { title: 'Citations', copy: 'Every claim in the draft is tied back to "Act, Section X" from the retrieved text.' },
]

// Placeholder domain set — swap in the real 12 categories from category_prototypes.py.
const LIBRARY_DOMAINS = [
  'Criminal law', 'Family law', 'Consumer protection', 'Labour & employment',
  'Property & real estate', 'Motor vehicles & accidents', 'Cyber law & IT',
  'Company & commercial law', 'Banking & finance', 'Constitutional & civil rights',
  'Environmental law', 'Taxation',
]

const EVAL_ROWS = [
  { label: 'Hit@3', value: 89.6, display: '89.6%' },
  { label: 'Hit@5', value: 100, display: '100%' },
  { label: 'MRR', value: 75.2, display: '0.752' },
]

const STACK_GROUPS = [
  { title: 'Frontend', items: ['React', 'Vite', 'Tailwind CSS', 'TypeScript'] },
  { title: 'Backend', items: ['Node.js', 'Express', 'TypeScript', 'Axios'] },
  { title: 'AI service', items: ['Python', 'FastAPI', 'ChromaDB', 'BM25', 'bge-m3', 'bge-reranker-v2-m3', 'Google Gemini'] },
]

/* ---- statute graph: sections of law as nodes, a few lit up mid-retrieval ---- */
const NODES: [number, number][] = [
  [80, 130], [190, 70], [310, 100], [370, 190], [260, 190],
  [150, 230], [70, 300], [210, 330], [330, 320], [300, 240], [130, 330],
]
const EDGES: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4], [4, 1], [4, 5], [5, 0],
  [5, 6], [6, 7], [7, 5], [7, 8], [8, 9], [9, 4], [9, 3], [7, 10], [10, 6],
]
const ACTIVE = new Set([1, 4, 8, 10])

function StatuteGraph() {
  return (
    <div className="relative mx-auto h-[280px] w-[280px] sm:h-[340px] sm:w-[340px]">
      <div
        className="absolute inset-0 rounded-full opacity-70 blur-[70px]"
        style={{ background: 'radial-gradient(circle, var(--violet-soft), transparent 65%)' }}
      />
      <svg viewBox="0 0 420 420" className="relative h-full w-full">
        {EDGES.map(([a, b], i) => (
          <line
            key={i}
            x1={NODES[a][0]} y1={NODES[a][1]}
            x2={NODES[b][0]} y2={NODES[b][1]}
            stroke="var(--line-strong)"
            strokeWidth="1"
          />
        ))}
        {NODES.map(([x, y], i) => {
          const active = ACTIVE.has(i)
          const delay = `${(i % 4) * 0.5}s`
          return (
            <g key={i}>
              {active && (
                <circle
                  className="node-halo"
                  cx={x} cy={y} r="5"
                  fill="var(--gold)"
                  style={{ animationDelay: delay }}
                />
              )}
              <circle
                className={active ? 'node-core' : undefined}
                cx={x} cy={y}
                r={active ? 4.5 : 3}
                fill={active ? 'var(--gold)' : 'var(--ink-faint)'}
                style={active ? { animationDelay: delay } : undefined}
              />
            </g>
          )
        })}
      </svg>
    </div>
  )
}

/** Small glowing dot used as a live/active indicator. */
function LiveDot({ color = 'var(--gold)' }: { color?: string }) {
  return (
    <span className="relative inline-flex h-2 w-2" style={{ color }}>
      <span className="pulse-ring absolute inline-flex h-2 w-2" />
      <span className="relative inline-flex h-2 w-2 rounded-full" style={{ background: color }} />
    </span>
  )
}

function SectionHeading({ eyebrow, title, lede }: { eyebrow: string; title: string; lede?: string }) {
  return (
    <div className="max-w-2xl">
      <p className="font-[var(--font-mono)] text-xs text-[var(--gold)]">{eyebrow}</p>
      <h2 className="mt-2 font-[var(--font-display)] text-4xl italic leading-tight text-[var(--ink)] sm:text-5xl">
        {title}
      </h2>
      {lede && <p className="mt-4 text-[15px] leading-relaxed text-[var(--ink-dim)]">{lede}</p>}
    </div>
  )
}

/** Static, non-interactive mockup used only in the hero. */
function ChatPreview() {
  return (
    <div className="chat-preview rise-in w-full max-w-sm p-5" style={{ animationDelay: '0.15s' }}>
      <div className="flex items-center gap-2">
        <Bot className="h-4 w-4" style={{ color: 'var(--gold)' }} />
        <span className="font-[var(--font-mono)] text-xs text-[var(--ink-faint)]">Legal Advisor</span>
        <span className="ml-auto"><LiveDot /></span>
      </div>

      <div className="mt-4 flex justify-end">
        <p className="chat-bubble-user max-w-[85%] px-3.5 py-2.5 text-sm">
          Can police arrest me without a warrant?
        </p>
      </div>

      <div className="relative mt-3 max-h-24 overflow-hidden">
        <p className="chat-bubble-ai px-3.5 py-2.5 text-sm leading-relaxed">
          Generally, no — but the law carves out specific exceptions, such as
          being caught committing certain offences or acting on a magistrate's
          order. Here's how that applies to your situation...
        </p>
        <div className="chat-fade absolute inset-x-0 bottom-0 h-10" />
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        <span className="chip px-2 py-1">BNSS · Sec. 35</span>
        <span className="chip px-2 py-1">BNSS · Sec. 41</span>
      </div>
      <p className="mt-3 text-[11px] text-[var(--ink-faint)]">Illustrative preview — scroll to ask for real.</p>
    </div>
  )
}

/** Relevance indicator: a thin gradient rule with the raw score in mono. */
function RelevanceBar({ score, delay }: { score: number | null; delay: number }) {
  const [width, setWidth] = useState(0)
  useEffect(() => {
    const pct = score != null ? Math.max(4, Math.min(100, Math.round(score * 100))) : 0
    const t = setTimeout(() => setWidth(pct), 120 + delay)
    return () => clearTimeout(t)
  }, [score, delay])

  return (
    <div className="rel-track flex-1">
      <div className="rel-fill" style={{ width: `${width}%` }} />
    </div>
  )
}

const STEPS = ['Query received', 'Retrieving statutes', 'Drafting answer']

function Tracker({ stage, found, elapsed }: {
  stage: 'retrieval' | 'generating'
  found: number | null
  elapsed: number
}) {
  const tip = TIPS[Math.floor(elapsed / 4) % TIPS.length]
  const activeIdx = stage === 'retrieval' ? 1 : 2

  return (
    <div className="panel rise-in relative mt-10 p-6 sm:p-7" aria-live="polite">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2 font-[var(--font-mono)] text-xs">
        {STEPS.map((label, i) => (
          <span key={label} className="flex items-center gap-3">
            <span className="step" data-active={i === activeIdx} data-done={i < activeIdx}>
              {label}
            </span>
            {i < STEPS.length - 1 && <span className="text-[var(--ink-faint)]">/</span>}
          </span>
        ))}
      </div>

      <div className="mt-4 flex items-center gap-3">
        <LiveDot />
        <p className="font-[var(--font-display)] text-xl italic text-[var(--ink)]">
          {stage === 'generating' ? 'Sections retrieved — drafting your answer' : 'Searching the statute index'}
        </p>
      </div>

      {found != null && (
        <p className="mt-1.5 text-sm text-[var(--ink-dim)]">Found {found} relevant sections</p>
      )}

      <div className="shimmer relative mt-5 h-[3px] w-full overflow-hidden rounded-full bg-[var(--line)]">
        <div
          className="h-full rounded-full"
          style={{
            width: `${Math.min(92, Math.max(8, Math.round((elapsed / 40) * 80) + 8))}%`,
            background: 'linear-gradient(90deg, var(--violet), var(--gold))',
          }}
        />
      </div>

      <div className="mt-3 flex items-center justify-between text-sm">
        <span className="text-[var(--ink-dim)]">{tip}</span>
        <span className="font-[var(--font-mono)] tabular-nums text-[var(--ink)]">{elapsed}s</span>
      </div>
    </div>
  )
}

export default function App() {
  const [query, setQuery] = useState('')
  const [stage, setStage] = useState<'retrieval' | 'generating' | null>(null)
  const [found, setFound] = useState<number | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const [result, setResult] = useState<AskResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (stage === 'generating') {
      timerRef.current = setInterval(() => setElapsed((s) => s + 1), 1000)
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [stage])

  async function run(queryText: string) {
    setStage('retrieval')
    setFound(null)
    setElapsed(0)
    setResult(null)
    setError(null)

    try {
      const result = await askStream(queryText, 8, (evt: StreamStage, data) => {
        if (evt === 'retrieval_done') {
          setFound(Number(data.count ?? 0))
          setStage('generating')
        }
        if (evt === 'error') {
          setError(typeof data.detail === 'string' ? data.detail : 'Backend error')
        }
      })

      setResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setStage(null)
    }
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!query.trim() || stage) return
    void run(query)
  }

  function onSample(q: string) {
    if (stage) return
    setQuery(q)
    void run(q)
  }

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--ink)]">
      <nav className="sticky top-0 z-40 border-b border-[var(--line)] bg-[var(--bg)]/85 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <a href="#hero" className="flex items-center gap-2.5">
            <span className="flex h-7 w-7 items-center justify-center rounded-full border border-[var(--line-strong)] bg-[var(--bg-2)]">
              <Scale className="h-3.5 w-3.5" style={{ color: 'var(--gold)' }} strokeWidth={1.8} />
            </span>
            <span className="font-[var(--font-display)] text-xl italic text-[var(--ink)]">Legal Advisor</span>
          </a>
          <div className="hidden items-center gap-6 md:flex">
            {NAV_LINKS.map((l) => (
              <a key={l.href} href={l.href} className="nav-link text-sm">{l.label}</a>
            ))}
          </div>
          <a href="#ask" className="btn-ask px-4 py-2 text-sm">Ask now</a>
        </div>
      </nav>

      <main className="mx-auto max-w-6xl px-6">

        {/* 1. Hero */}
        <section id="hero" className="grid grid-cols-1 items-center gap-10 pt-16 pb-6 lg:grid-cols-[3fr_2fr] lg:gap-12 lg:pt-24">
          <div className="rise-in">
            <h1 className="max-w-xl font-[var(--font-display)] text-[3rem] italic leading-[1.05] text-[var(--ink)] sm:text-[4rem]">
              Understand Indian law. Ask in plain English.
            </h1>
            <p className="mt-6 max-w-md text-[1.05rem] leading-relaxed text-[var(--ink-dim)]">
              Legal Advisor retrieves the exact Acts and Sections behind your
              question, reranks them for precision, and drafts a grounded
              answer — citations included, nothing invented.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <a href="#ask" className="btn-ask px-7 py-3.5">Ask now</a>
              <a href="#how-it-works" className="btn-ghost px-6 py-3.5 text-sm">See how it works</a>
            </div>
          </div>
          <div className="flex justify-center lg:justify-end">
            <ChatPreview />
          </div>
        </section>

        {/* 2. Key Stats */}
        <Reveal
          as="section"
          id="stats"
          effect="zoom"
          className="mt-16 grid grid-cols-2 gap-8 sm:grid-cols-4 reveal-stagger"
        >
          {KEY_STATS.map((s) => (
            <div key={s.label}>
              <p className="stat-figure text-4xl sm:text-5xl">{s.value}</p>
              <p className="mt-1.5 text-[13px] text-[var(--ink-dim)]">{s.label}</p>
            </div>
          ))}
        </Reveal>

        {/* 3. About */}
        <Reveal as="section" id="about" effect="left" className="mt-28 grid grid-cols-1 gap-10 lg:grid-cols-[2fr_1fr]">
          <SectionHeading
            eyebrow="about"
            title="A RAG pipeline built on primary legislation"
            lede="Legal Advisor is a retrieval-augmented generation system for Indian statutes. It ingests Acts, Codes, and Sanhitas, chunks them section by section, indexes them with hybrid dense and lexical search, reranks candidates with a cross-encoder, and passes only the top sections to Gemini to draft a plain-language, cited answer."
          />
          <div className="panel panel-accent flex items-start gap-3 p-5">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" style={{ color: 'var(--gold)' }} />
            <p className="text-[13px] leading-relaxed text-[var(--ink-dim)]">
              Not legal advice. Legal Advisor surfaces statute text for
              informational purposes — it doesn't replace a licensed legal
              professional.
            </p>
          </div>
        </Reveal>

        {/* 4. Ask a Question */}
        <section id="ask" className="mt-28">
          <Reveal effect="up">
            <SectionHeading
              eyebrow="try it"
              title="Ask a question"
              lede="Type your own, or start from a sample query. Every answer cites the sections retrieved beneath it."
            />
          </Reveal>

          <form onSubmit={onSubmit} className="mt-9 flex flex-col gap-3 sm:flex-row">
            <div className="field flex flex-1 items-center gap-3 px-4 py-3.5">
              <Search className="h-4 w-4 shrink-0 text-[var(--ink-faint)]" />
              <label htmlFor="query" className="sr-only">Describe your legal question</label>
              <input
                id="query"
                className="w-full bg-transparent text-[15px] text-[var(--ink)] outline-none placeholder:text-[var(--ink-faint)]"
                placeholder="e.g. can police arrest me without a warrant?"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={!!stage}
              />
            </div>
            <button type="submit" disabled={!query.trim() || !!stage} className="btn-ask justify-center px-7 py-3.5">
              {stage ? (stage === 'generating' ? `Drafting… ${elapsed}s` : 'Searching…') : 'Ask'}
            </button>
          </form>

          <div className="mt-6 flex flex-wrap items-center gap-2">
            <span className="text-sm text-[var(--ink-faint)]">Or start with</span>
            {SAMPLE_QUERIES.map((q) => (
              <button key={q} type="button" onClick={() => onSample(q)} disabled={!!stage} className="docket-tag px-3.5 py-1.5 text-sm">
                {q}
              </button>
            ))}
          </div>

          {stage && <Tracker stage={stage} found={found} elapsed={elapsed} />}

          {error && (
            <div className="rise-in mt-10 rounded-2xl border border-[var(--burgundy)]/35 bg-[var(--burgundy-soft)] p-5">
              <p className="text-sm font-medium text-[#e08484]">The request didn't go through.</p>
              <p className="mt-1 whitespace-pre-wrap text-sm text-[var(--ink-dim)]">{error}</p>
            </div>
          )}

          {result && (
            <div className="mt-10 grid grid-cols-1 gap-6 lg:grid-cols-3">
              <div className="panel panel-accent rise-in p-7 sm:p-9 lg:col-span-2">
                <div className="markdown text-[15.5px]">
                  <ReactMarkdown>{result.answer}</ReactMarkdown>
                </div>
                <p className="mt-8 border-t border-[var(--line)] pt-4 font-[var(--font-mono)] text-xs text-[var(--ink-faint)]">
                  model — {result.model}
                </p>
              </div>

              <aside className="panel rise-in p-6" style={{ animationDelay: '0.08s' }}>
                <h3 className="font-[var(--font-display)] text-xl italic text-[var(--ink)]">Sources</h3>
                <ol className="mt-4 space-y-3">
                  {result.sources.map((s, i) => {
                    const score = typeof s.final_score === 'number' ? s.final_score : null
                    return (
                      <li key={i} className="source-item p-3.5">
                        <div className="flex items-start gap-2.5">
                          <span
                            className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full font-[var(--font-mono)] text-[10px] font-medium"
                            style={{ background: 'var(--gold-soft)', color: 'var(--gold)' }}
                          >
                            {i + 1}
                          </span>
                          <p className="min-w-0 flex-1 text-sm font-medium leading-snug text-[var(--ink)]">
                            {s.citation}
                          </p>
                        </div>
                        <div className="mt-2.5 flex items-center gap-2 pl-7.5">
                          <RelevanceBar score={score} delay={i * 60} />
                          <span className="font-[var(--font-mono)] text-[11px] text-[var(--ink)]">
                            {score != null ? score.toFixed(3) : s.final_score}
                          </span>
                        </div>
                      </li>
                    )
                  })}
                </ol>
              </aside>
            </div>
          )}
        </section>

        {/* 5. How It Works */}
        <section id="how-it-works" className="mt-28">
          <Reveal effect="blur">
            <SectionHeading
              eyebrow="pipeline"
              title="How it works"
              lede="Five stages turn a plain-English question into a cited answer."
            />
          </Reveal>
          <div className="mt-12 grid grid-cols-1 items-start gap-10 lg:grid-cols-[3fr_2fr]">
            <ol className="relative grid grid-cols-1 gap-4 sm:grid-cols-5 sm:gap-3">
              <div className="absolute top-6 hidden h-px w-full flow-line sm:block" aria-hidden />
              {FLOW_STEPS.map((step, i) => (
                <Reveal as="li" key={step.title} effect="flip" delay={i * 100} className="flow-node relative p-4">
                  <span className="flow-index">{String(i + 1).padStart(2, '0')}</span>
                  <p className="mt-2 font-[var(--font-display)] text-lg italic text-[var(--ink)]">{step.title}</p>
                  <p className="mt-1.5 text-[12.5px] leading-relaxed text-[var(--ink-dim)]">{step.copy}</p>
                </Reveal>
              ))}
            </ol>
            <Reveal effect="zoom-out" delay={200}>
              <StatuteGraph />
              <p className="mx-auto mt-4 max-w-xs text-center text-[13px] leading-relaxed text-[var(--ink-dim)]">
                Each node is a statute section. Hybrid search narrows up to 80
                candidates; the gold nodes are what the reranker confirms and
                carries into the final top 8.
              </p>
            </Reveal>
          </div>
        </section>

        {/* 6. Key Features */}
        <Reveal as="section" id="features" effect="right" className="mt-28 grid grid-cols-1 gap-8 sm:grid-cols-3 reveal-stagger">
          {FEATURES.map(({ icon: Icon, tag, title, copy }) => (
            <div key={title}>
              <div className="flex items-center justify-between">
                <Icon className="h-5 w-5" style={{ color: 'var(--gold)' }} strokeWidth={1.7} />
                <span className="font-[var(--font-mono)] text-xs text-[var(--ink-dim)]">{tag}</span>
              </div>
              <p className="mt-4 font-[var(--font-display)] text-2xl italic text-[var(--ink)]">{title}</p>
              <p className="mt-2 text-[14px] leading-relaxed text-[var(--ink-dim)]">{copy}</p>
            </div>
          ))}
        </Reveal>

        {/* 7. Legal Library */}
        <section id="library" className="mt-28">
          <Reveal effect="rotate">
            <SectionHeading
              eyebrow="library"
              title="Browse by domain"
              lede="37 statutes, grouped into 12 legal domains. Placeholder labels below — swap in the real category list from category_prototypes.py."
            />
          </Reveal>
          <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {LIBRARY_DOMAINS.map((d, i) => (
              <Reveal as="a" key={d} href="#ask" effect="zoom" delay={(i % 4) * 60} className="library-card flex items-center gap-2.5 px-4 py-3.5">
                <Library className="h-4 w-4 shrink-0" style={{ color: 'var(--violet)' }} />
                <span className="text-sm text-[var(--ink)]">{d}</span>
              </Reveal>
            ))}
          </div>
        </section>

        {/* 8. Evaluation */}
        <section id="evaluation" className="mt-28">
          <Reveal effect="down">
            <SectionHeading
              eyebrow="evaluation"
              title="Measured against 192 test cases"
              lede="Retrieval quality with the reranker and anchor boost enabled."
            />
          </Reveal>
          <Reveal effect="down" className="panel mt-8 p-6 sm:p-8" delay={100}>
            <div className="space-y-5">
              {EVAL_ROWS.map((row) => (
                <div key={row.label} className="flex items-center gap-4">
                  <span className="w-14 shrink-0 font-[var(--font-mono)] text-sm text-[var(--ink-dim)]">{row.label}</span>
                  <div className="rel-track flex-1">
                    <div className="rel-fill" style={{ width: `${row.value}%` }} />
                  </div>
                  <span className="w-16 shrink-0 text-right font-[var(--font-mono)] text-sm font-medium text-[var(--ink)]">
                    {row.display}
                  </span>
                </div>
              ))}
            </div>
          </Reveal>
        </section>

        {/* 9. Example Answer */}
        <section id="example" className="mt-28">
          <Reveal effect="flip">
            <SectionHeading eyebrow="example" title="What an answer looks like" />
          </Reveal>
          <Reveal className="panel panel-accent mt-8 p-7 sm:p-9" delay={100}>
            <div className="flex items-center justify-between">
              <p className="font-[var(--font-mono)] text-xs text-[var(--ink-faint)]">sample — not a live query</p>
              <MessageSquare className="h-4 w-4" style={{ color: 'var(--ink-faint)' }} />
            </div>
            <p className="mt-4 font-[var(--font-display)] text-2xl italic text-[var(--ink)]">
              "Can police arrest me without a warrant?"
            </p>
            <div className="markdown mt-5 text-[15px]">
              <p>
                Generally, no. Police in India need a warrant for most
                arrests, but the law defines specific situations where an
                arrest without one is permitted — such as being caught
                committing certain offences, or under a magistrate's written
                order.
              </p>
              <p>
                If you're arrested without a warrant, you're entitled to be
                told the grounds for arrest and produced before a magistrate
                within 24 hours.
              </p>
            </div>
            <div className="mt-5 flex flex-wrap gap-2">
              <span className="chip px-2.5 py-1.5">BNSS · Section 35</span>
              <span className="chip px-2.5 py-1.5">BNSS · Section 41</span>
              <span className="chip px-2.5 py-1.5">BNSS · Section 58</span>
            </div>
          </Reveal>
        </section>

        {/* 10. Technology Stack */}
        <section id="stack" className="mt-28">
          <Reveal>
            <SectionHeading eyebrow="stack" title="Technology" lede="Three services, each doing one job well." />
          </Reveal>
          <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-3">
            {STACK_GROUPS.map((g, i) => (
              <Reveal key={g.title} effect={i % 2 === 0 ? 'left' : 'right'} delay={i * 100} className="panel p-6">
                <div className="flex items-center gap-2">
                  <Boxes className="h-4 w-4" style={{ color: 'var(--gold)' }} />
                  <p className="font-[var(--font-display)] text-lg italic text-[var(--ink)]">{g.title}</p>
                </div>
                <div className="mt-4 flex flex-wrap gap-1.5">
                  {g.items.map((item) => (
                    <span key={item} className="stack-pill px-2.5 py-1">{item}</span>
                  ))}
                </div>
              </Reveal>
            ))}
          </div>
        </section>

        {/* 11. Performance */}
        <section id="performance" className="mt-28">
          <Reveal>
            <SectionHeading eyebrow="performance" title="Response times" />
          </Reveal>
          <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2">
            <Reveal effect="zoom" className="panel p-6">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4" style={{ color: 'var(--violet)' }} />
                <p className="text-sm text-[var(--ink-dim)]">First request after startup</p>
              </div>
              <p className="stat-figure mt-3 text-3xl">~20–30s <span className="text-lg not-italic text-[var(--ink-dim)]">warmup</span></p>
              <p className="mt-1 text-sm text-[var(--ink-dim)]">plus ~40–70s generation</p>
            </Reveal>
            <Reveal effect="zoom" delay={100} className="panel p-6">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4" style={{ color: 'var(--gold)' }} />
                <p className="text-sm text-[var(--ink-dim)]">Subsequent requests</p>
              </div>
              <p className="stat-figure mt-3 text-3xl">~3–5s <span className="text-lg not-italic text-[var(--ink-dim)]">retrieval</span></p>
              <p className="mt-1 text-sm text-[var(--ink-dim)]">plus ~30–40s generation</p>
            </Reveal>
          </div>
        </section>

        {/* 12. Disclaimer */}
        <Reveal as="section" id="disclaimer" effect="blur" className="mt-28">
          <div className="panel-warn rounded-2xl p-7 sm:p-9">
            <div className="flex items-center gap-2.5">
              <AlertTriangle className="h-5 w-5" style={{ color: '#e08484' }} />
              <p className="font-[var(--font-display)] text-2xl italic text-[var(--ink)]">Not legal advice</p>
            </div>
            <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-[var(--ink-dim)]">
              This tool surfaces the text of statutes for informational
              purposes. It does not substitute for a licensed legal
              professional, and it does not account for the specific facts of
              your situation. For anything with real consequences, consult a
              lawyer.
            </p>
          </div>
        </Reveal>

        {/* 13. Final CTA */}
        <Reveal as="section" id="cta" effect="rotate" className="mt-28 flex flex-col items-center py-16 text-center">
          <Network className="h-6 w-6" style={{ color: 'var(--violet)' }} />
          <p className="mt-5 max-w-lg font-[var(--font-display)] text-4xl italic leading-tight text-[var(--ink)] sm:text-5xl">
            Have a legal question? Ask Legal Advisor.
          </p>
          <a href="#ask" className="btn-ask mt-8 px-8 py-4">Ask now</a>
        </Reveal>
      </main>

      {/* 14. Footer */}
      <footer className="mt-20 border-t border-[var(--line)]">
        <div className="mx-auto max-w-6xl px-6 py-12">
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-[2fr_1fr_1fr]">
            <div>
              <div className="flex items-center gap-2.5">
                <Scale className="h-4 w-4" style={{ color: 'var(--gold)' }} />
                <span className="font-[var(--font-display)] text-lg italic text-[var(--ink)]">Legal Advisor</span>
              </div>
              <p className="mt-3 max-w-xs text-sm leading-relaxed text-[var(--ink-dim)]">
                A RAG system that retrieves and cites Indian statute text —
                37 Acts, 12 domains, grounded answers.
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-[var(--ink)]">Explore</p>
              <div className="mt-3 flex flex-col gap-2">
                {[...NAV_LINKS, { href: '#ask', label: 'Ask a question' }].map((l) => (
                  <a key={l.href} href={l.href} className="nav-link text-sm">{l.label}</a>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-[var(--ink)]">Project</p>
              <div className="mt-3 flex flex-col gap-2 text-sm text-[var(--ink-dim)]">
                <span>Retrieval Hit@5: 100%</span>
                <span>MRR: 0.752</span>
                <span>192 labeled test cases</span>
              </div>
            </div>
          </div>
          <p className="mt-10 border-t border-[var(--line)] pt-6 text-[12.5px] text-[var(--ink-faint)]">
            Not legal advice. This tool surfaces the text of statutes for
            informational purposes — it does not substitute for a licensed
            legal professional.
          </p>
        </div>
      </footer>
    </div>
  )
}