"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
} from "lucide-react";
import {
  useTasks,
  useTaskStats,
  useStartTask,
  useCancelTask,
  useDeleteTask,
} from "@/hooks/use-tasks";
import { formatDistanceToNow } from "date-fns";
import { zhCN } from "date-fns/locale";
import { CreateTaskDialog } from "@/components/tasks/create-task-dialog";

const statusConfig: Record<
  string,
  { label: string; color: string; progressColor: string; icon: React.ReactNode }
> = {
  pending: {
    label: "等待中",
    color: "bg-warning/10 text-warning-foreground border-warning/20",
    progressColor: "bg-warning",
    icon: <Clock className="h-3.5 w-3.5" />,
  },
  running: {
    label: "运行中",
    color: "bg-primary/10 text-primary border-primary/20",
    progressColor: "bg-primary",
    icon: <Loader2 className="h-3.5 w-3.5 animate-spin" />,
  },
  success: {
    label: "已完成",
    color: "bg-success/10 text-success border-success/20",
    progressColor: "bg-success",
    icon: <CheckCircle className="h-3.5 w-3.5" />,
  },
  failed: {
    label: "失败",
    color: "bg-destructive/10 text-destructive border-destructive/20",
    progressColor: "bg-destructive",
    icon: <XCircle className="h-3.5 w-3.5" />,
  },
  cancelled: {
    label: "已取消",
    color: "bg-muted text-muted-foreground border-border",
    progressColor: "bg-muted-foreground",
    icon: <Square className="h-3.5 w-3.5" />,
  },
};

const taskTypeLabels: Record<string, string> = {
  job_crawl: "招聘采集",
  rent_crawl: "房租采集",
  forum_crawl: "论坛采集",
  public_data: "公开数据",
};

interface StatCardProps {
  title: string;
  value: number;
  icon: typeof Clock;
  color: string;
}

function StatCard({ title, value, icon: Icon, color }: StatCardProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center gap-3">
          <div className={cn("p-2 rounded-lg", color)}>
            <Icon className="h-4 w-4" />
          </div>
          <div>
            <div className="text-2xl font-bold">{value}</div>
            <p className="text-sm text-muted-foreground">{title}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function TasksPage() {
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const { data: tasks, isLoading, refetch } = useTasks();
  const { data: stats } = useTaskStats();
  const startTask = useStartTask();
  const cancelTask = useCancelTask();
  const deleteTask = useDeleteTask();

  const handleStart = async (id: string) => {
    await startTask.mutateAsync(id);
  };

  const handleCancel = async (id: string) => {
    await cancelTask.mutateAsync(id);
  };

  const handleDelete = async (id: string) => {
    await deleteTask.mutateAsync(id);
  };

  const getStatusBadge = (status: string) => {
    const config = statusConfig[status] || statusConfig.pending;
    return (
      <Badge variant="outline" className={cn("gap-1", config.color)}>
        {config.icon}
        {config.label}
      </Badge>
    );
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
            <StatCard
              title="等待中"
              value={stats.pending}
              icon={Clock}
              color="bg-warning/10 text-warning"
            />
            <StatCard
              title="运行中"
              value={stats.running}
              icon={Loader2}
              color="bg-primary/10 text-primary"
            />
            <StatCard
              title="已完成"
              value={stats.success}
              icon={CheckCircle}
              color="bg-success/10 text-success"
            />
            <StatCard
              title="失败"
              value={stats.failed}
              icon={XCircle}
              color="bg-destructive/10 text-destructive"
            />
            <StatCard
              title="采集记录"
              value={stats.total_records}
              icon={Database}
              color="bg-chart-4/10 text-chart-4"
            />
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle>
              任务列表
              {tasks && tasks.length > 0 && (
                <span className="ml-2 text-sm font-normal text-muted-foreground">
                  共 {tasks.length} 个任务
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
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
                  <TableRow>
                    <TableHead>类型</TableHead>
                    <TableHead>数据源</TableHead>
                    <TableHead>城市</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead>进度</TableHead>
                    <TableHead>记录数</TableHead>
                    <TableHead>创建时间</TableHead>
                    <TableHead className="text-right">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tasks.map((task) => {
                    const config =
                      statusConfig[task.status] || statusConfig.pending;
                    return (
                      <TableRow key={task.id}>
                        <TableCell>
                          <Badge variant="outline">
                            {taskTypeLabels[task.task_type] || task.task_type}
                          </Badge>
                        </TableCell>
                        <TableCell>{task.data_source_name || "-"}</TableCell>
                        <TableCell>{task.city_name || "全部"}</TableCell>
                        <TableCell>
                          <div className="flex flex-col gap-1">
                            {getStatusBadge(task.status)}
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
                          <div className="flex items-center gap-2 min-w-[100px]">
                            <Progress
                              value={task.progress}
                              className={cn("h-2", `[&>div]:${config.progressColor}`)}
                            />
                            <span className="text-sm text-muted-foreground w-10">
                              {task.progress}%
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>{task.records_count}</TableCell>
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
          </CardContent>
        </Card>
      </div>

      <CreateTaskDialog open={isCreateOpen} onOpenChange={setIsCreateOpen} />
    </AppLayout>
  );
}
