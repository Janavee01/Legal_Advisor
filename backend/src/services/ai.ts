import axios from "axios";
import { env } from "../config";

export interface RetrieveSource {
  citation: string;
  act_name: string;
  section_number: string;
  section_title: string;
  chapter: string;
  category: string;
  source: string;
  final_score: number;
}

export interface AnswerResult {
  query: string;
  answer: string;
  model: string;
  usage: Record<string, unknown> | null;
  finish_reason: string | null;
  sources: RetrieveSource[];
}

export interface RetrieveResult {
  query: string;
  results: RetrieveSource[];
}

const client = axios.create({
  baseURL: env.aiServiceUrl,
  timeout: 180_000,
});

export async function ask(query: string, topK = 5): Promise<AnswerResult> {
  const { data } = await client.post<AnswerResult>("/answer", {
    query,
    top_k: topK,
  });
  return data;
}

export async function retrieveAi(
  query: string,
  topK = 5,
): Promise<RetrieveResult> {
  const { data } = await client.post<RetrieveResult>("/retrieve", {
    query,
    top_k: topK,
  });
  return data;
}
