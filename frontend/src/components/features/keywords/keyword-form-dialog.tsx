"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import type { Keyword } from "@/types";
import { useCreateKeyword, useUpdateKeyword } from "@/hooks/use-keywords";

const keywordSchema = z.object({
  category: z.enum(["job_search", "job_exclude", "forum_topic"]),
  keyword: z.string().min(1, "请输入关键词"),
  priority: z.enum(["core", "extended"]),
  enabled: z.boolean(),
});

type KeywordFormData = z.infer<typeof keywordSchema>;

interface KeywordFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  keyword?: Keyword | null;
}

const categoryOptions = [
  { value: "job_search", label: "招聘搜索关键词" },
  { value: "job_exclude", label: "招聘排除关键词" },
  { value: "forum_topic", label: "论坛话题关键词" },
];

const priorityOptions = [
  { value: "core", label: "核心（优先采集）" },
  { value: "extended", label: "扩展（可选采集）" },
];

export function KeywordFormDialog({
  open,
  onOpenChange,
  keyword,
}: KeywordFormDialogProps) {
  const createKeyword = useCreateKeyword();
  const updateKeyword = useUpdateKeyword();
  const isEditing = !!keyword;

  const form = useForm<KeywordFormData>({
    resolver: zodResolver(keywordSchema),
    defaultValues: {
      category: "job_search",
      keyword: "",
      priority: "extended",
      enabled: true,
    },
  });

  useEffect(() => {
    if (keyword) {
      form.reset({
        category: keyword.category,
        keyword: keyword.keyword,
        priority: keyword.priority,
        enabled: keyword.enabled,
      });
    } else {
      form.reset({
        category: "job_search",
        keyword: "",
        priority: "extended",
        enabled: true,
      });
    }
  }, [keyword, form]);

  const onSubmit = async (data: KeywordFormData) => {
    try {
      if (isEditing && keyword) {
        await updateKeyword.mutateAsync({ id: keyword.id, data });
      } else {
        await createKeyword.mutateAsync(data);
      }
      onOpenChange(false);
    } catch {
      // Error handled by mutation
    }
  };

  const isLoading = createKeyword.isPending || updateKeyword.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{isEditing ? "编辑关键词" : "添加关键词"}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="category"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>关键词类型</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                    value={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="选择关键词类型" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {categoryOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="keyword"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>关键词</FormLabel>
                  <FormControl>
                    <Input placeholder="例如：Python、远程" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="priority"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>优先级</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                    value={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="选择优先级" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {priorityOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="enabled"
              render={({ field }) => (
                <FormItem className="flex items-center justify-between rounded-lg border p-3">
                  <div className="space-y-0.5">
                    <FormLabel>启用状态</FormLabel>
                    <p className="text-sm text-muted-foreground">
                      启用后将用于数据采集
                    </p>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-2 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                取消
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? "保存中..." : isEditing ? "更新" : "添加"}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
