/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Message } from "./Message";
export type ChatRequest = {
  thread_id?: number | null;
  session_id?: string | null;
  query: string;
  history?: Array<Message>;
  pro_search?: boolean;
};
