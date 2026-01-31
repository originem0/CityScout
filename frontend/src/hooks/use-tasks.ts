"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  CrawlTask,
  CrawlTaskCreate,
  CrawlTaskUpdate,
  BatchTaskCreate,
  TaskStats,
} from "@/types";
import { toast } from "sonner";

interface TaskListParams {
  status?: string;
  task_type?: string;
  city_id?: number;
  data_source_id?: number;
  skip?: number;
  limit?: number;
}

export function useTasks(params?: TaskListParams) {
  return useQuery({
    queryKey: ["tasks", params],
    queryFn: () => api.tasks.list(params),
    refetchInterval: 5000, // Auto-refresh every 5 seconds for running tasks
  });
}

export function useTask(id: string) {
  return useQuery({
    queryKey: ["tasks", id],
    queryFn: () => api.tasks.get(id),
    enabled: !!id,
    refetchInterval: (query) =>
      query.state.data?.status === "running" ? 2000 : false, // Faster refresh for running tasks
  });
}

export function useTaskStats() {
  return useQuery({
    queryKey: ["tasks", "stats"],
    queryFn: () => api.tasks.stats(),
    refetchInterval: 10000,
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CrawlTaskCreate) => api.tasks.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      toast.success("任务创建成功");
    },
    onError: (error: Error) => {
      toast.error(`创建失败: ${error.message}`);
    },
  });
}

export function useCreateBatchTasks() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BatchTaskCreate) => api.tasks.createBatch(data),
    onSuccess: (tasks) => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      toast.success(`成功创建 ${tasks.length} 个任务`);
    },
    onError: (error: Error) => {
      toast.error(`批量创建失败: ${error.message}`);
    },
  });
}

export function useUpdateTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CrawlTaskUpdate }) =>
      api.tasks.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
    onError: (error: Error) => {
      toast.error(`更新失败: ${error.message}`);
    },
  });
}

export function useDeleteTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.tasks.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      toast.success("任务已删除");
    },
    onError: (error: Error) => {
      toast.error(`删除失败: ${error.message}`);
    },
  });
}

export function useStartTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.tasks.start(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      toast.success("任务已启动");
    },
    onError: (error: Error) => {
      toast.error(`启动失败: ${error.message}`);
    },
  });
}

export function useCancelTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.tasks.cancel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      toast.success("任务已取消");
    },
    onError: (error: Error) => {
      toast.error(`取消失败: ${error.message}`);
    },
  });
}
