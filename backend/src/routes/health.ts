import { Router } from "express";
import axios from "axios";
import { env } from "../config";

export const healthRouter = Router();

healthRouter.get("/health", async (_req, res) => {
  let aiService = "down";

  try {
    const { data } = await axios.get(`${env.aiServiceUrl}/health`, {
      timeout: 5_000,
    });
    if (data?.status === "ok") aiService = "ok";
  } catch {
    /* ai down */
  }

  res.json({ status: "ok", aiService });
});
