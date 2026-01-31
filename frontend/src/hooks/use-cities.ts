"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { City, CityCreate, CityUpdate } from "@/types";
import { toast } from "sonner";

export function useCities(params?: { enabled?: boolean; tier?: string }) {
  return useQuery({
    queryKey: ["cities", params],
    queryFn: () => api.cities.list(params),
  });
}

export function useCity(id: number) {
  return useQuery({
    queryKey: ["cities", id],
    queryFn: () => api.cities.get(id),
    enabled: !!id,
  });
}

export function useCreateCity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CityCreate) => api.cities.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cities"] });
      toast.success("城市添加成功");
    },
    onError: (error: Error) => {
      toast.error(`添加失败: ${error.message}`);
    },
  });
}

export function useUpdateCity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: CityUpdate }) =>
      api.cities.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cities"] });
      toast.success("城市更新成功");
    },
    onError: (error: Error) => {
      toast.error(`更新失败: ${error.message}`);
    },
  });
}

export function useDeleteCity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.cities.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cities"] });
      toast.success("城市删除成功");
    },
    onError: (error: Error) => {
      toast.error(`删除失败: ${error.message}`);
    },
  });
}

export function useToggleCity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.cities.toggle(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["cities"] });
      toast.success(data.enabled ? "城市已启用" : "城市已禁用");
    },
    onError: (error: Error) => {
      toast.error(`操作失败: ${error.message}`);
    },
  });
}
