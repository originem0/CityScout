"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { DataSourceCreate, DataSourceUpdate } from "@/types";
import { toast } from "sonner";

export function useDataSources(params?: { type?: string; enabled?: boolean }) {
  return useQuery({
    queryKey: ["sources", params],
    queryFn: () => api.sources.list(params),
  });
}

export function useCreateDataSource() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: DataSourceCreate) => api.sources.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sources"] });
      toast.success("数据源添加成功");
    },
    onError: (error: Error) => {
      toast.error(`添加失败: ${error.message}`);
    },
  });
}

export function useUpdateDataSource() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: DataSourceUpdate }) =>
      api.sources.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sources"] });
      toast.success("数据源更新成功");
    },
    onError: (error: Error) => {
      toast.error(`更新失败: ${error.message}`);
    },
  });
}

export function useDeleteDataSource() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.sources.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sources"] });
      toast.success("数据源删除成功");
    },
    onError: (error: Error) => {
      toast.error(`删除失败: ${error.message}`);
    },
  });
}

export function useToggleDataSource() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.sources.toggle(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["sources"] });
      toast.success(data.enabled ? "数据源已启用" : "数据源已禁用");
    },
    onError: (error: Error) => {
      toast.error(`操作失败: ${error.message}`);
    },
  });
}
