"use client";

import { cn } from "@/lib/utils";
import { useConfigStore } from "@/stores";
import { Switch } from "./ui/switch";
import { env } from "@/env.mjs";
import { memo } from "react";

/**
 * Toggle component for enabling/disabling expert (pro search) mode
 */
const ProToggle = () => {
  const { proMode, toggleProMode } = useConfigStore();

  return (
    <div 
      className="group flex space-x-2 items-center justify-end pr-3 hover:text-primary"
      title="Expert mode creates a plan to answer your question for more accurate results"
    >
      <Switch
        disabled={!env.NEXT_PUBLIC_PRO_MODE_ENABLED}
        checked={proMode}
        onCheckedChange={toggleProMode}
      />
      <span
        className={cn(
          "font-medium text-sm transition-all",
          proMode ? "text-tint" : "text-gray-500 group-hover:text-primary",
        )}
      >
        Expert
      </span>
    </div>
  );
};

export default memo(ProToggle);
