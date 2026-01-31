"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { KeywordCreate, KeywordUpdate } from "@/types";
import { toast } from "sonner";

export function useKeywords(params?: {
  category?: string;
  enabled?: boolean;
  priority?: string;
}) {
  return useQuery({
    queryKey: ["keywords", params],
    queryFn: () => api.keywords.list(params),
  });
}

export function useCreateKeyword() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: KeywordCreate) => api.keywords.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["keywords"] });
      toast.success("关键词添加成功");
    },
    onError: (error: Error) => {
      toast.error(`添加失败: ${error.message}`);
    },
  });
}

export function useUpdateKeyword() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: KeywordUpdate }) =>
      api.keywords.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["keywords"] });
      toast.success("关键词更新成功");
    },
    onError: (error: Error) => {
      toast.error(`更新失败: ${error.message}`);
    },
  });
}

export function useDeleteKeyword() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.keywords.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["keywords"] });
      toast.success("关键词删除成功");
    },
    onError: (error: Error) => {
      toast.error(`删除失败: ${error.message}`);
    },
  });
}
