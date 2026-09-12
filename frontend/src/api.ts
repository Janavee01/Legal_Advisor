export interface Source {
  citation: string;
  act_name: string;
  section_number: string;
  section_title: string;
  final_score: number;
}

export interface AskResponse {
  query: string;
  answer: string;
  model: string;
  usage: Record<string, unknown> | null;
  finish_reason: string | null;
  sources: Source[];
}

export type StreamStage =
  | 'retrieval_started'
  | 'retrieval_done'
  | 'generation_started'
  | 'generation_done'
  | 'error';

export async function ask(query: string, topK = 8): Promise<AskResponse> {
  const res = await fetch('/api/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, top_k: topK }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Backend error ${res.status}: ${text.slice(0, 300)}`);
  }

  return res.json();
}

/**
 * Streams the answer with stage updates from the backend:
 * retrieval_started -> retrieval_done -> generation_started -> generation_done.
 */
export async function askStream(
  query: string,
  topK: number,
  onEvent: (stage: StreamStage, data: Record<string, unknown>) => void,
): Promise<AskResponse> {
  const res = await fetch('/api/ask/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, top_k: topK }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Backend error ${res.status}: ${text.slice(0, 300)}`);
  }

  if (!res.body) throw new Error('Streaming not supported by this browser');

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let result: AskResponse | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const frames = buffer.split('\n\n');
    buffer = frames.pop() ?? '';

    for (const frame of frames) {
      const lines = frame.split('\n');
      let stage: StreamStage = 'generation_done';
      let dataStr = '{}';

      for (const line of lines) {
        if (line.startsWith('event: ')) stage = line.slice(7) as StreamStage;
        if (line.startsWith('data: ')) dataStr = line.slice(6);
      }

      try {
        const data = JSON.parse(dataStr) as Record<string, unknown>;
        onEvent(stage, data);
        if (stage === 'generation_done') result = data as unknown as AskResponse;
      } catch {
        // skip any partial/malformed frame
      }
    }
  }

  if (!result) throw new Error('Stream ended without an answer');
  return result;
}