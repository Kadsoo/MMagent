import { useEffect, useState } from "react";
import { getTools } from "../services/api";
import type { ToolSpec } from "../types/api";

export function useTools() {
  const [tools, setTools] = useState<ToolSpec[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    getTools()
      .then((data) => {
        if (mounted) {
          setTools(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Failed to load tools");
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, []);

  return { tools, loading, error };
}

