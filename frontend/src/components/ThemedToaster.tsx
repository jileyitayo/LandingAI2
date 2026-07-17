"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Toaster } from "sonner";

export function ThemedToaster() {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  return (
    <Toaster
      position="top-right"
      richColors
      theme={mounted && resolvedTheme === "dark" ? "dark" : "light"}
    />
  );
}
