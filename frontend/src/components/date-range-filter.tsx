"use client";

import { useState } from "react";
import { format } from "date-fns";
import { Calendar as CalendarIcon, X } from "lucide-react";
import { useChatStore } from "@/stores";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

/**
 * Date range filter component with calendar picker
 * Allows filtering search results by custom date range
 */
export const DateRangeFilter = ({ scale = 100 }: { scale?: number }) => {
  const { startDate, endDate, setStartDate, setEndDate, clearDateRange } = useChatStore();
  const [isOpen, setIsOpen] = useState(false);

  // Parse dates for calendar
  const startDateObj = startDate ? new Date(startDate) : undefined;
  const endDateObj = endDate ? new Date(endDate) : undefined;

  const hasActiveRange = startDate || endDate;

  const getTooltipText = () => {
    if (!hasActiveRange) return "Filter by date range";

    if (startDate && endDate) {
      return `${format(new Date(startDate), "MMM d, yyyy")} - ${format(new Date(endDate), "MMM d, yyyy")}`;
    } else if (startDate) {
      return `From ${format(new Date(startDate), "MMM d, yyyy")}`;
    } else {
      return `Until ${format(new Date(endDate!), "MMM d, yyyy")}`;
    }
  };

  const handleStartDateSelect = (date: Date | undefined) => {
    if (date) {
      setStartDate(format(date, "yyyy-MM-dd"));
    } else {
      setStartDate(null);
    }
  };

  const handleEndDateSelect = (date: Date | undefined) => {
    if (date) {
      setEndDate(format(date, "yyyy-MM-dd"));
    } else {
      setEndDate(null);
    }
  };

  return (
    <div className="flex items-center gap-1">
      <Popover open={isOpen} onOpenChange={setIsOpen} modal={true}>
        <PopoverTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className={cn(
              "relative",
              hasActiveRange && "text-primary hover:text-primary"
            )}
            title={getTooltipText()}
          >
            <CalendarIcon className="h-4 w-4" />
            {hasActiveRange && (
              <span className="absolute -top-0.5 -right-0.5 h-2 w-2 rounded-full bg-primary" />
            )}
          </Button>
        </PopoverTrigger>
      <PopoverContent className={`w-auto p-0 max-h-[85vh] overflow-y-auto scale-[${scale}%]`} align="start" sideOffset={8}>
        <div className="flex flex-col gap-2 p-2 sm:p-3">
          <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
            <div className="space-y-1.5">
              <div className="text-xs sm:text-sm font-medium px-1">Start Date</div>
              <Calendar
                mode="single"
                className="text-xs scale-90 sm:scale-100 origin-top-left"
                captionLayout="dropdown"
                selected={startDateObj}
                onSelect={handleStartDateSelect}
                disabled={(date) =>
                  date > new Date() || (endDateObj ? date > endDateObj : false)
                }
                fromYear={2000}
                toYear={new Date().getFullYear()}
              />
            </div>

            <div className="space-y-1.5">
              <div className="text-xs sm:text-sm font-medium px-1">End Date</div>
              <Calendar
                mode="single"
                className="text-xs scale-90 sm:scale-100 origin-top-left"
                captionLayout="dropdown"
                selected={endDateObj}
                onSelect={handleEndDateSelect}
                disabled={(date) =>
                  date > new Date() || (startDateObj ? date < startDateObj : false)
                }
                fromYear={2000}
                toYear={new Date().getFullYear()}
              />
            </div>
          </div>

          <div className="flex gap-2 pt-2 border-t">
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={() => {
                clearDateRange();
                setIsOpen(false);
              }}
            >
              Clear
            </Button>
            <Button
              type="button"
              size="sm"
              className="flex-1"
              onClick={() => setIsOpen(false)}
              disabled={!hasActiveRange}
            >
              Apply
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
      {hasActiveRange && (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          title="Clear date range"
          onClick={clearDateRange}
        >
          <X className="h-3 w-3" />
        </Button>
      )}
    </div>
  );
};
