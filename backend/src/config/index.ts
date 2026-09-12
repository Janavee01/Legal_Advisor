import "dotenv/config";

export const env = {
  port: Number(process.env.PORT || 3001),
  aiServiceUrl: process.env.AI_SERVICE_URL || "http://localhost:8000",
};
