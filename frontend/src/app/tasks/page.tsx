"use client";

import { useState, useMemo } from "react";
import { AppLayout } from "@/components/layout";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { PageHeader } from "@/components/common/page-header";
import { EmptyState } from "@/components/common/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import {
  RefreshCw,
  Play,
  Square,
  Trash2,
  Plus,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  ListTodo,
  Database,
  Wifi,
  WifiOff,
} from "lucide-react";
import {
  useTasks,
  useTaskStats,
  useStartTask,
  useCancelTask,
  useDeleteTask,
} from "@/hooks/use-tasks";
import { useRunningTasksProgress } from "@/hooks/use-task-progress-ws";
import { formatDistanceToNow } from "date-fns";
import { zhCN } from "date-fns/locale";
import { CreateTaskDialog } from "@/components/tasks/create-task-dialog";
import type { CrawlTask, TaskProgressData } from "@/types";

const statusConfig: Record<
  string,
  { label: string; bg: string; progressColor: string; icon: typeof Clock }
> = {
  pending: {
    label: "等待",
    bg: "bg-warning",
    progressColor: "bg-warning",
    icon: Clock,
  },
  running: {
    label: "运行",
    bg: "bg-primary",
    progressColor: "bg-primary",
    icon: Loader2,
  },
  success: {
    label: "成功",
    bg: "bg-success",
    progressColor: "bg-success",
    icon: CheckCircle,
  },
  failed: {
    label: "失败",
    bg: "bg-destructive",
    progressColor: "bg-destructive",
    icon: XCircle,
  },
  cancelled: {
    label: "取消",
    bg: "bg-muted-foreground",
    progressColor: "bg-muted-foreground",
    icon: Square,
  },
};

const taskTypeLabels: Record<string, string> = {
  job_crawl: "招聘采集",
  rent_crawl: "房租采集",
  forum_crawl: "论坛采集",
  public_data: "公开数据",
  company_review: "公司评价",
  salary_stats: "薪资统计",
};

const taskStateLabels: Record<string, string> = {
  init: "初始化",
  connecting: "连接中",
  loading: "加载页面",
  parsing: "解析数据",
  saving: "保存数据",
  paginating: "翻页中",
  completed: "已完成",
  failed: "失败",
};

interface StatCardProps {
  title: string;
  value: number;
  icon: typeof Clock;
  accent: string;
}

function StatCard({ title, value, icon: Icon, accent }: StatCardProps) {
  return (
    <div className="group bg-card rounded-lg border shadow-soft card-hover p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-muted-foreground font-medium">
            {title}
          </p>
          <p className="text-3xl font-bold mt-1 tabular-nums">{value}</p>
        </div>
        <div className={cn("p-2.5 rounded-lg", accent)}>
          <Icon className="h-5 w-5 text-white" />
        </div>
      </div>
    </div>
  );
}

interface TaskProgressCellProps {
  task: CrawlTask;
  wsProgress: TaskProgressData | undefined;
}

function TaskProgressCell({ task, wsProgress }: TaskProgressCellProps) {
  const config = statusConfig[task.status] || statusConfig.pending;
  const isRunning = task.status === "running";

  const progress = isRunning && wsProgress ? wsProgress.progress : task.progress;
  const currentPage = wsProgress?.current_page;
  const totalPages = wsProgress?.total_pages;
  const itemsFound = wsProgress?.items_found;
  const currentState = wsProgress?.current_state;

  return (
    <div className="flex flex-col gap-1 min-w-[120px]">
      <div className="flex items-center gap-2">
        <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
          <div
            className={cn("h-full rounded-full transition-all duration-500", config.progressColor)}
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="text-sm text-muted-foreground tabular-nums w-10">
          {progress}%
        </span>
      </div>
      {isRunning && wsProgress && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          {currentState && (
            <span className="text-primary font-medium">
              {taskStateLabels[currentState] || currentState}
            </span>
          )}
          {currentPage !== undefined && currentPage > 0 && (
            <span>
              第 {currentPage}{totalPages ? `/${totalPages}` : ""} 页
            </span>
          )}
          {itemsFound !== undefined && itemsFound > 0 && (
            <span>已找到 {itemsFound}</span>
          )}
        </div>
      )}
    </div>
  );
}

export default function TasksPage() {
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const { data: tasks, isLoading, refetch } = useTasks();
  const { data: stats } = useTaskStats();
  const startTask = useStartTask();
  const cancelTask = useCancelTask();
  const deleteTask = useDeleteTask();

  const runningTaskIds = useMemo(() => {
    return tasks?.filter((t) => t.status === "running").map((t) => t.id) || [];
  }, [tasks]);

  const wsProgressMap = useRunningTasksProgress(runningTaskIds);

  const handleStart = async (id: string) => {
    await startTask.mutateAsync(id);
  };

  const handleCancel = async (id: string) => {
    await cancelTask.mutateAsync(id);
  };

  const handleDelete = async (id: string) => {
    await deleteTask.mutateAsync(id);
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <PageHeader
          icon={ListTodo}
          title="任务管理"
          description="创建和管理爬虫采集任务"
          actions={
            <>
              <Button variant="outline" size="icon" onClick={() => refetch()}>
                <RefreshCw className="h-4 w-4" />
              </Button>
              <Button onClick={() => setIsCreateOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                创建任务
              </Button>
            </>
          }
        />

        {/* Stats Cards */}
        {stats && (
          <div className="grid gap-4 md:grid-cols-5">
            <StatCard title="等待中" value={stats.pending} icon={Clock} accent="bg-warning" />
            <StatCard title="运行中" value={stats.running} icon={Loader2} accent="bg-primary" />
            <StatCard title="已完成" value={stats.success} icon={CheckCircle} accent="bg-success" />
            <StatCard title="失败" value={stats.failed} icon={XCircle} accent="bg-destructive" />
            <StatCard title="采集记录" value={stats.total_records} icon={Database} accent="bg-chart-4" />
          </div>
        )}

        <div className="bg-card rounded-lg border shadow-soft">
          <div className="flex items-center justify-between p-6 border-b border-border">
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-semibold">任务列表</h2>
              {tasks && tasks.length > 0 && (
                <span className="text-sm text-muted-foreground">
                  共 {tasks.length} 个任务
                </span>
              )}
            </div>
            {runningTaskIds.length > 0 && (
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 rounded-full border border-primary/20">
                <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                <span className="text-sm text-primary font-medium">
                  {runningTaskIds.length} 个运行中
                </span>
              </div>
            )}
          </div>
          <div className="p-6">
            {isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-4 py-3">
                    <Skeleton className="h-6 w-20" />
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-4 w-16" />
                    <Skeleton className="h-2 w-32" />
                    <Skeleton className="h-8 w-20 ml-auto" />
                  </div>
                ))}
              </div>
            ) : tasks && tasks.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="text-xs font-medium text-muted-foreground">类型</TableHead>
                    <TableHead className="text-xs font-medium text-muted-foreground">数据源</TableHead>
                    <TableHead className="text-xs font-medium text-muted-foreground">城市</TableHead>
                    <TableHead className="text-xs font-medium text-muted-foreground">状态</TableHead>
                    <TableHead className="text-xs font-medium text-muted-foreground">进度</TableHead>
                    <TableHead className="text-xs font-medium text-muted-foreground">记录数</TableHead>
                    <TableHead className="text-xs font-medium text-muted-foreground">创建时间</TableHead>
                    <TableHead className="text-right text-xs font-medium text-muted-foreground">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tasks.map((task) => {
                    const wsProgress = wsProgressMap[task.id];
                    const hasWsConnection = !!wsProgress;
                    const config = statusConfig[task.status] || statusConfig.pending;
                    const StatusIcon = config.icon;

                    const recordsCount =
                      task.status === "running" && wsProgress
                        ? wsProgress.records_count
                        : task.records_count;

                    return (
                      <TableRow key={task.id} className="hover:bg-muted/50">
                        <TableCell>
                          <span className="text-sm font-medium">
                            {taskTypeLabels[task.task_type] || task.task_type}
                          </span>
                        </TableCell>
                        <TableCell>{task.data_source_name || "-"}</TableCell>
                        <TableCell>{task.city_name || "全部"}</TableCell>
                        <TableCell>
                          <div className="flex flex-col gap-1">
                            <div className="flex items-center gap-1.5">
                              <div className={cn("flex items-center gap-1.5 px-2 py-0.5 rounded-md", config.bg)}>
                                <StatusIcon
                                  className={cn(
                                    "h-3 w-3 text-white",
                                    task.status === "running" && "animate-spin"
                                  )}
                                />
                                <span className="text-xs font-medium text-white">
                                  {config.label}
                                </span>
                              </div>
                              {task.status === "running" && (
                                <TooltipProvider>
                                  <Tooltip>
                                    <TooltipTrigger>
                                      {hasWsConnection ? (
                                        <Wifi className="h-3 w-3 text-success" />
                                      ) : (
                                        <WifiOff className="h-3 w-3 text-muted-foreground" />
                                      )}
                                    </TooltipTrigger>
                                    <TooltipContent>
                                      {hasWsConnection ? "实时连接" : "等待连接"}
                                    </TooltipContent>
                                  </Tooltip>
                                </TooltipProvider>
                              )}
                            </div>
                            {task.error_message && (
                              <span
                                className="text-xs text-destructive cursor-help max-w-[200px] truncate"
                                title={task.error_message}
                              >
                                {task.error_message}
                              </span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <TaskProgressCell task={task} wsProgress={wsProgress} />
                        </TableCell>
                        <TableCell className="tabular-nums">{recordsCount}</TableCell>
                        <TableCell className="text-muted-foreground text-sm">
                          {formatDistanceToNow(new Date(task.created_at), {
                            addSuffix: true,
                            locale: zhCN,
                          })}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1">
                            {task.status === "pending" && (
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleStart(task.id)}
                                disabled={startTask.isPending}
                                title="启动任务"
                              >
                                <Play className="h-4 w-4" />
                              </Button>
                            )}
                            {(task.status === "pending" ||
                              task.status === "running") && (
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleCancel(task.id)}
                                disabled={cancelTask.isPending}
                                title="取消任务"
                              >
                                <Square className="h-4 w-4" />
                              </Button>
                            )}
                            {(task.status === "pending" ||
                              task.status === "failed" ||
                              task.status === "cancelled") && (
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleDelete(task.id)}
                                disabled={deleteTask.isPending}
                                title="删除任务"
                                className="text-destructive hover:text-destructive"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            ) : (
              <EmptyState
                icon={ListTodo}
                title="暂无任务"
                description="创建爬虫任务开始采集城市数据"
                action={{
                  label: "创建第一个任务",
                  onClick: () => setIsCreateOpen(true),
                  icon: Plus,
                }}
              />
            )}
          </div>
        </div>
      </div>

      <CreateTaskDialog open={isCreateOpen} onOpenChange={setIsCreateOpen} />
    </AppLayout>
  );
}
