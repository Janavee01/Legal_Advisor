import express from "express";
import cors from "cors";

import { env } from "./config";
import { healthRouter } from "./routes/health";
import { askRouter } from "./routes/ask";
import { retrieveRouter } from "./routes/retrieve";

const app = express();

app.use(cors());
app.use(express.json());

app.use("/api", healthRouter);
app.use("/api", askRouter);
app.use("/api", retrieveRouter);

// eslint-disable-next-line @typescript-eslint/no-unused-vars
app.use((err: unknown, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  const message =
    err instanceof Error ? err.message : String(err);

  console.error("Unhandled error:", message);
  res.status(500).json({ error: message });
});

app.listen(env.port, () => {
  console.log(
    `Backend listening on :${env.port} → AI service: ${env.aiServiceUrl}`,
  );
});
