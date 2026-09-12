import { Router } from "express";
import axios from "axios";
import { ask } from "../services/ai";
import { env } from "../config";

export const askRouter = Router();

const AI_SERVICE_URL = env.aiServiceUrl;

function validTopK(raw: unknown): number {
  const n = Number(raw);
  return Number.isFinite(n) && n >= 1 && n <= 20 ? n : 8;
}

askRouter.post("/ask", async (req, res) => {
  const query = typeof req.body?.query === "string"
    ? req.body.query.trim()
    : "";

  if (!query) {
    res.status(400).json({ error: "query is required" });
    return;
  }

  try {
    const result = await ask(query, validTopK(req.body?.top_k));
    res.json(result);
  } catch (err) {
    const detail = axios.isAxiosError(err)
      ? (err.response?.data as { detail?: string })?.detail || err.message
      : err instanceof Error
        ? err.message
        : String(err);

    res.status(502).json({ error: "AI service error", detail });
  }
});

askRouter.post("/ask/stream", async (req, res) => {
  const query = typeof req.body?.query === "string"
    ? req.body.query.trim()
    : "";

  if (!query) {
    res.status(400).json({ error: "query is required" });
    return;
  }

  const topK = validTopK(req.body?.top_k);

  try {
    const upstream = await fetch(`${AI_SERVICE_URL}/answer/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k: topK }),
    });

    if (!upstream.ok || !upstream.body) {
      const detail = (await upstream.text()).slice(0, 300);
      res.status(502).json({ error: "AI service error", detail });
      return;
    }

    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache, no-transform");
    res.setHeader("Connection", "keep-alive");
    res.setHeader("X-Accel-Buffering", "no");
    res.flushHeaders();

    const reader = upstream.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      res.write(decoder.decode(value, { stream: true }));
    }

    res.end();
  } catch (err) {
    const detail = err instanceof Error ? err.message : String(err);
    if (!res.headersSent) {
      res.status(502).json({ error: "AI service error", detail });
    } else {
      res.end();
    }
  }
});
