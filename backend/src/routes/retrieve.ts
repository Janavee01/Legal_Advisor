import { Router } from "express";
import axios from "axios";
import { retrieveAi } from "../services/ai";

export const retrieveRouter = Router();

retrieveRouter.post("/retrieve", async (req, res) => {
  const query = typeof req.body?.query === "string"
    ? req.body.query.trim()
    : "";

  if (!query) {
    res.status(400).json({ error: "query is required" });
    return;
  }

  const topK = Number(req.body?.top_k ?? 5);

  try {
    const result = await retrieveAi(
      query,
      Number.isFinite(topK) && topK >= 1 && topK <= 20 ? topK : 5,
    );
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
