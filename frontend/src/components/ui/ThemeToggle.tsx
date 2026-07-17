"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Sun, Monitor, Moon } from "lucide-react";

const options = [
  { value: "light", label: "Light", Icon: Sun },
  { value: "system", label: "System", Icon: Monitor },
  { value: "dark", label: "Dark", Icon: Moon },
] as const;

export function ThemeToggle({ compact = false }: { compact?: boolean }) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  return (
    <div
      role="radiogroup"
      aria-label="Theme"
      className={`inline-flex items-center rounded-full border border-border bg-card-muted p-1 ${
        compact ? "gap-0" : "gap-1"
      }`}
    >
      {options.map(({ value, label, Icon }) => {
        const active = mounted && theme === value;
        return (
          <button
            key={value}
            type="button"
            role="radio"
            aria-checked={active}
            title={label}
            onClick={() => setTheme(value)}
            className={`inline-flex items-center justify-center gap-1.5 rounded-full transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/50 ${
              compact ? "px-2.5 py-1.5" : "px-4 py-1.5 text-sm font-medium"
            } ${
              active
                ? "bg-card text-brand shadow-sm ring-1 ring-border"
                : "text-muted hover:text-fg"
            }`}
          >
            <Icon className="h-4 w-4" aria-hidden="true" />
            {!compact && label}
          </button>
        );
      })}
    </div>
  );
}
