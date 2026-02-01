"use client";

import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { useQueryClient } from "@tanstack/react-query";
import type { TaskProgressData, WsMessage } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getWsUrl(taskId: string): string {
  // Convert http(s) to ws(s)
  const wsBase = API_BASE_URL.replace(/^http/, "ws");
  return `${wsBase}/api/v1/ws/tasks/${taskId}/progress`;
}

interface UseTaskProgressWsOptions {
  enabled?: boolean;
  onComplete?: (data: TaskProgressData) => void;
  onError?: (error: string) => void;
}

interface UseTaskProgressWsReturn {
  progress: TaskProgressData | null;
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  reconnect: () => void;
}

export function useTaskProgressWs(
  taskId: string | null,
  options: UseTaskProgressWsOptions = {}
): UseTaskProgressWsReturn {
  const { enabled = true, onComplete, onError } = options;

  const [progress, setProgress] = useState<TaskProgressData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const queryClient = useQueryClient();

  const cleanup = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setIsConnecting(false);
  }, []);

  const connect = useCallback(() => {
    if (!taskId || !enabled) return;

    cleanup();
    setIsConnecting(true);
    setError(null);

    const ws = new WebSocket(getWsUrl(taskId));
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setIsConnecting(false);
      setError(null);
      reconnectAttemptsRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const message: WsMessage = JSON.parse(event.data);

        switch (message.type) {
          case "initial":
          case "progress":
            setProgress(message.data);
            break;

          case "completed":
            setProgress(message.data);
            // Invalidate task queries to refresh the list
            queryClient.invalidateQueries({ queryKey: ["tasks"] });
            onComplete?.(message.data);
            break;

          case "error":
            setError(message.message);
            onError?.(message.message);
            break;

          case "heartbeat":
            // Ignore heartbeats
            break;
        }
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
      }
    };

    ws.onerror = () => {
      setError("WebSocket connection error");
      setIsConnected(false);
    };

    ws.onclose = (event) => {
      setIsConnected(false);
      setIsConnecting(false);

      // Don't reconnect if closed normally or task completed
      if (event.code === 1000 || event.code === 4004) {
        return;
      }

      // Exponential backoff reconnect (max 5 attempts)
      if (reconnectAttemptsRef.current < 5 && enabled) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
        reconnectAttemptsRef.current++;

        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      }
    };
  }, [taskId, enabled, cleanup, queryClient, onComplete, onError]);

  const reconnect = useCallback(() => {
    reconnectAttemptsRef.current = 0;
    connect();
  }, [connect]);

  useEffect(() => {
    if (taskId && enabled) {
      connect();
    }

    return cleanup;
  }, [taskId, enabled, connect, cleanup]);

  return {
    progress,
    isConnected,
    isConnecting,
    error,
    reconnect,
  };
}

// Hook for tracking multiple running tasks
export function useRunningTasksProgress(taskIds: string[]) {
  const [progressMap, setProgressMap] = useState<Record<string, TaskProgressData>>({});
  const queryClient = useQueryClient();

  // Create a stable key for the taskIds array to avoid unnecessary reconnections
  const taskIdsKey = useMemo(() => {
    const sorted = [...taskIds].sort();
    return JSON.stringify(sorted);
  }, [taskIds]);

  useEffect(() => {
    if (taskIds.length === 0) {
      setProgressMap({});
      return;
    }

    const sockets: WebSocket[] = [];

    taskIds.forEach((taskId) => {
      const ws = new WebSocket(getWsUrl(taskId));
      sockets.push(ws);

      ws.onmessage = (event) => {
        try {
          const message: WsMessage = JSON.parse(event.data);

          if (message.type === "initial" || message.type === "progress" || message.type === "completed") {
            setProgressMap((prev) => ({
              ...prev,
              [taskId]: message.data,
            }));

            if (message.type === "completed") {
              queryClient.invalidateQueries({ queryKey: ["tasks"] });
            }
          }
        } catch (e) {
          console.error("Failed to parse WebSocket message:", e);
        }
      };

      ws.onerror = () => {
        console.error(`WebSocket error for task ${taskId}`);
      };

      ws.onclose = () => {
        // Remove from progress map when connection closes
        setProgressMap((prev) => {
          const newMap = { ...prev };
          delete newMap[taskId];
          return newMap;
        });
      };
    });

    return () => {
      sockets.forEach((ws) => {
        if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
          ws.close();
        }
      });
    };
  }, [taskIdsKey, queryClient]);

  return progressMap;
}
