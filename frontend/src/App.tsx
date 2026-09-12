import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { askStream } from './api'
import type { StreamStage } from './api'
import type { AskResponse } from './api'

const SAMPLE_QUERIES = [
  'My employer is not paying my salary',
  'Can police arrest me without a warrant?',
  'Can I get a refund for a defective product?',
  'I met with a road accident — what are my rights?',
  'Someone forged my documents, what can I do?',
]

const STAGE_MESSAGES: Record<string, string> = {
  retrieval_started: 'Searching the legal database…',
  retrieval_done: 'Sections found — ranking relevance…',
  generation_started: 'Generating your grounded answer…',
}

const TIPS = [
  'Every claim cites Act · Section from real statute text',
  'Answers are grounded in the retrieved sections',
  'Retrieval: BM25 + dense embeddings + reranking',
  'Sources shown with relevance scores below',
]

function Loading({ stage, found, elapsed }: {
  stage: 'retrieval' | 'generating'
  found: number | null
  elapsed: number
}) {
  const tip = TIPS[Math.floor(elapsed / 4) % TIPS.length]
  const progress = Math.min(90, Math.max(6, Math.round((elapsed / 40) * 78) + 6))

  return (
    <div className="mt-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <span className="relative flex h-3 w-3">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75" />
          <span className="relative inline-flex h-3 w-3 rounded-full bg-blue-600" />
        </span>
        <p className="font-medium">
          {stage === 'retrieval' ? STAGE_MESSAGES.retrieval_started : STAGE_MESSAGES.generation_started}
        </p>
      </div>

      {found != null && (
        <p className="mt-2 text-sm text-emerald-700">
          Found {found} relevant legal sections ✓
        </p>
      )}

      <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-[width] duration-1000 ease-linear"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="mt-3 flex items-center justify-between text-sm text-slate-500">
        <span className="animate-pulse italic">{tip}</span>
        <span className="font-mono tabular-nums">{elapsed}s</span>
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
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-2xl px-4 py-12">
        <h1 className="text-3xl font-bold">Legal Advisor</h1>
        <p className="mt-1 text-slate-600">
          Ask about Indian law — grounded in the actual statutes.
        </p>

        <div className="mt-4 flex flex-wrap gap-2">
          {SAMPLE_QUERIES.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => onSample(q)}
              disabled={!!stage}
              className="rounded-full border border-slate-300 bg-white px-3 py-1 text-sm text-slate-600 shadow-sm hover:border-blue-400 hover:text-blue-700 disabled:opacity-50"
            >
              {q}
            </button>
          ))}
        </div>

        <form onSubmit={onSubmit} className="mt-6 flex gap-2">
          <input
            className="flex-1 rounded-lg border border-slate-300 bg-white px-4 py-2 shadow-sm outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g. can police arrest me without a warrant?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={!!stage}
          />
          <button
            type="submit"
            disabled={!query.trim() || !!stage}
            className="rounded-lg bg-blue-600 px-5 py-2 font-medium text-white shadow-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {stage ? stage === 'generating' ? `Generating… ${elapsed}s` : 'Searching…' : 'Ask'}
          </button>
        </form>

        {stage && <Loading stage={stage} found={found} elapsed={elapsed} />}

        {error && (
          <p className="mt-4 rounded-lg bg-red-50 p-3 text-red-700 whitespace-pre-wrap">
            {error}
          </p>
        )}

        {result && (
          <div className="mt-6 space-y-4">
            <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <div className="markdown text-[15px] leading-relaxed">
                <ReactMarkdown>{result.answer}</ReactMarkdown>
              </div>
            </div>

            <div>
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                Sources
              </h2>
              <ul className="mt-2 space-y-1">
                {result.sources.map((s, i) => (
                  <li
                    key={i}
                    className="rounded-md bg-white px-3 py-2 text-sm shadow-sm"
                  >
                    <div className="font-medium">{s.citation}</div>
                    <div className="mt-0.5 text-xs text-slate-500">
                      relevance score: {typeof s.final_score === 'number' ? s.final_score.toFixed(3) : s.final_score}
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            <p className="text-xs text-slate-400">model: {result.model}</p>
          </div>
        )}
      </div>
    </main>
  )
}