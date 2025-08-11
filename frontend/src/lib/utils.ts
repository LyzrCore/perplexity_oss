import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { ChatModel } from "../generated";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function isLocalModel(model: string) {
  return false; // No local models in Lyzr-only setup
}

export function isCloudModel(model: string) {
  return true; // All Lyzr models are cloud-based
}
