"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { useCreateTask, useCreateBatchTasks } from "@/hooks/use-tasks";
import { useDataSources } from "@/hooks/use-sources";
import { useCities } from "@/hooks/use-cities";
import { useKeywords } from "@/hooks/use-keywords";
import type { TaskType } from "@/types";

const taskSchema = z.object({
  task_type: z.enum(["job_crawl", "rent_crawl", "forum_crawl", "public_data"]),
  data_source_id: z.number().optional(),
  city_id: z.number().optional(),
  keyword_id: z.number().optional(),
  batch_mode: z.boolean(),
});

type TaskFormData = z.infer<typeof taskSchema>;

interface CreateTaskDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const taskTypeOptions = [
  { value: "job_crawl", label: "招聘采集", description: "采集招聘网站岗位数据" },
  { value: "rent_crawl", label: "房租采集", description: "采集租房网站价格数据" },
  { value: "forum_crawl", label: "论坛采集", description: "采集论坛城市评价" },
  { value: "public_data", label: "公开数据", description: "采集公开统计数据" },
];

export function CreateTaskDialog({ open, onOpenChange }: CreateTaskDialogProps) {
  const createTask = useCreateTask();
  const createBatchTasks = useCreateBatchTasks();
  const { data: sources } = useDataSources();
  const { data: cities } = useCities({ enabled: true });
  const { data: keywords } = useKeywords();

  const form = useForm<TaskFormData>({
    resolver: zodResolver(taskSchema),
    defaultValues: {
      task_type: "job_crawl",
      batch_mode: false,
    },
  });

  const watchTaskType = form.watch("task_type");
  const watchBatchMode = form.watch("batch_mode");

  // Filter sources by task type
  const filteredSources = sources?.filter((s) => {
    const typeMap: Record<string, string> = {
      job_crawl: "job",
      rent_crawl: "rent",
      forum_crawl: "forum",
      public_data: "public_data",
    };
    return s.type === typeMap[watchTaskType] && s.enabled;
  });

  // Filter keywords by task type
  const filteredKeywords = keywords?.filter((k) => {
    if (watchTaskType === "job_crawl") {
      return k.category === "job_search" && k.enabled;
    }
    if (watchTaskType === "forum_crawl") {
      return k.category === "forum_topic" && k.enabled;
    }
    return false;
  });

  const onSubmit = async (data: TaskFormData) => {
    try {
      if (data.batch_mode && data.data_source_id) {
        // Batch mode: create tasks for all enabled cities
        await createBatchTasks.mutateAsync({
          task_type: data.task_type as TaskType,
          data_source_id: data.data_source_id,
          keyword_id: data.keyword_id,
        });
      } else {
        // Single task mode
        await createTask.mutateAsync({
          task_type: data.task_type as TaskType,
          data_source_id: data.data_source_id,
          city_id: data.city_id,
          keyword_id: data.keyword_id,
        });
      }
      form.reset();
      onOpenChange(false);
    } catch {
      // Error handled by mutation
    }
  };

  const isLoading = createTask.isPending || createBatchTasks.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>创建采集任务</DialogTitle>
          <DialogDescription>
            选择任务类型和参数，创建新的数据采集任务
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="task_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>任务类型</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                    value={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="选择任务类型" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {taskTypeOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          <div>
                            <span>{option.label}</span>
                            <span className="ml-2 text-xs text-muted-foreground">
                              {option.description}
                            </span>
                          </div>
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
              name="data_source_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>数据源</FormLabel>
                  <Select
                    onValueChange={(v) => field.onChange(parseInt(v))}
                    value={field.value?.toString()}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="选择数据源" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {filteredSources?.map((source) => (
                        <SelectItem
                          key={source.id}
                          value={source.id.toString()}
                        >
                          {source.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    {filteredSources?.length === 0 &&
                      "没有可用的数据源，请先启用对应类型的数据源"}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="batch_mode"
              render={({ field }) => (
                <FormItem className="flex items-center justify-between rounded-lg border p-3">
                  <div className="space-y-0.5">
                    <FormLabel>批量模式</FormLabel>
                    <FormDescription>
                      启用后将为所有已启用城市创建任务
                    </FormDescription>
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

            {!watchBatchMode && (
              <FormField
                control={form.control}
                name="city_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>目标城市</FormLabel>
                    <Select
                      onValueChange={(v) => field.onChange(parseInt(v))}
                      value={field.value?.toString()}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="选择城市（可选）" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {cities?.map((city) => (
                          <SelectItem key={city.id} value={city.id.toString()}>
                            {city.name} ({city.province})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            {filteredKeywords && filteredKeywords.length > 0 && (
              <FormField
                control={form.control}
                name="keyword_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>关键词</FormLabel>
                    <Select
                      onValueChange={(v) => field.onChange(parseInt(v))}
                      value={field.value?.toString()}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="选择关键词（可选）" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {filteredKeywords.map((kw) => (
                          <SelectItem key={kw.id} value={kw.id.toString()}>
                            {kw.keyword}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            <div className="flex justify-end gap-2 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                取消
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading
                  ? "创建中..."
                  : watchBatchMode
                    ? `批量创建 (${cities?.length || 0} 个城市)`
                    : "创建任务"}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
