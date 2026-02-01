"use client";

import { AppLayout } from "@/components/layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/common/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import {
  MapPin,
  Briefcase,
  Home,
  MessageSquare,
  ListTodo,
  BarChart3,
  Upload,
  FileDown,
  ArrowRight,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  Zap,
  TrendingUp,
  Database,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { cn } from "@/lib/utils";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface DashboardData {
  counts: {
    cities: number;
    keywords: number;
    sources: number;
    jobs: number;
    rent: number;
    forum: number;
    total_data: number;
  };
  task_stats: {
    pending: number;
    running: number;
    success: number;
    failed: number;
    total: number;
  };
  recent_tasks: {
    id: string;
    task_type: string;
    status: string;
    progress: number;
    records_count: number;
    created_at: string;
    error_message: string | null;
  }[];
}

const taskTypeLabels: Record<string, string> = {
  job_crawl: "招聘采集",
  rent_crawl: "租房采集",
  forum_crawl: "论坛采集",
  public_data: "公共数据",
};

const statusConfig: Record<
  string,
  { label: string; bg: string; icon: typeof Clock }
> = {
  pending: { label: "等待", bg: "bg-warning", icon: Clock },
  running: { label: "运行", bg: "bg-primary", icon: Loader2 },
  success: { label: "成功", bg: "bg-success", icon: CheckCircle2 },
  failed: { label: "失败", bg: "bg-destructive", icon: XCircle },
  cancelled: { label: "取消", bg: "bg-muted-foreground", icon: XCircle },
};

const quickLinks = [
  { name: "创建任务", href: "/tasks", icon: ListTodo, accent: "bg-primary" },
  { name: "导入数据", href: "/manual-import", icon: Upload, accent: "bg-chart-4" },
  { name: "数据分析", href: "/analysis", icon: BarChart3, accent: "bg-success" },
  { name: "导出报告", href: "/export", icon: FileDown, accent: "bg-chart-3" },
];

interface StatCardProps {
  title: string;
  value: number | string;
  icon: typeof MapPin;
  accent: string;
  isLoading?: boolean;
}

function StatCard({ title, value, icon: Icon, accent, isLoading }: StatCardProps) {
  return (
    <div className="group bg-card rounded-lg border shadow-soft card-hover p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-muted-foreground font-medium">
            {title}
          </p>
          {isLoading ? (
            <Skeleton className="h-10 w-24 mt-2" />
          ) : (
            <p className="text-3xl font-bold mt-1 tabular-nums">{value}</p>
          )}
        </div>
        <div className={cn("p-2.5 rounded-lg", accent)}>
          <Icon className="h-5 w-5 text-white" />
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { data, isLoading } = useQuery<DashboardData>({
    queryKey: ["dashboard"],
    queryFn: async () => {
      const res = await fetch(`${API_BASE_URL}/api/v1/dashboard/overview`);
      if (!res.ok) throw new Error("Failed to fetch dashboard");
      return res.json();
    },
    refetchInterval: 30000,
  });

  const counts = data?.counts;
  const taskStats = data?.task_stats;
  const recentTasks = data?.recent_tasks || [];

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Hero Header */}
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <Zap className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h1 className="text-xl font-semibold tracking-tight">仪表盘</h1>
                <p className="text-sm text-muted-foreground">城市数据采集与分析概览</p>
              </div>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-2 text-sm">
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-success/10 rounded-full border border-success/20">
              <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
              <span className="text-success font-medium">系统运行中</span>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="目标城市"
            value={counts?.cities ?? "-"}
            icon={MapPin}
            accent="bg-primary"
            isLoading={isLoading}
          />
          <StatCard
            title="招聘岗位"
            value={counts?.jobs?.toLocaleString() ?? "-"}
            icon={Briefcase}
            accent="bg-chart-1"
            isLoading={isLoading}
          />
          <StatCard
            title="房源信息"
            value={counts?.rent?.toLocaleString() ?? "-"}
            icon={Home}
            accent="bg-chart-3"
            isLoading={isLoading}
          />
          <StatCard
            title="论坛帖子"
            value={counts?.forum?.toLocaleString() ?? "-"}
            icon={MessageSquare}
            accent="bg-chart-2"
            isLoading={isLoading}
          />
        </div>

        {/* Main Content */}
        <div className="grid gap-6 lg:grid-cols-5">
          {/* Task Stats - 3 columns */}
          <div className="lg:col-span-3 bg-card rounded-lg border shadow-soft p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <ListTodo className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-semibold">任务统计</h2>
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Database className="h-4 w-4" />
                <span className="tabular-nums font-medium">
                  {counts?.total_data?.toLocaleString() ?? 0} 条数据
                </span>
              </div>
            </div>

            {isLoading ? (
              <div className="grid grid-cols-4 gap-4">
                {[...Array(4)].map((_, i) => (
                  <Skeleton key={i} className="h-20" />
                ))}
              </div>
            ) : taskStats ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: "等待中", value: taskStats.pending, color: "bg-warning" },
                  { label: "运行中", value: taskStats.running, color: "bg-primary" },
                  { label: "已完成", value: taskStats.success, color: "bg-success" },
                  { label: "失败", value: taskStats.failed, color: "bg-destructive" },
                ].map((stat) => (
                  <div key={stat.label} className="relative bg-muted rounded-md p-4">
                    <div className={cn("absolute left-0 top-0 bottom-0 w-1 rounded-l-md", stat.color)} />
                    <p className="text-xs text-muted-foreground">
                      {stat.label}
                    </p>
                    <p className="text-2xl font-bold mt-1 tabular-nums">{stat.value}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground">暂无数据</p>
            )}

            {/* Total bar */}
            {taskStats && taskStats.total > 0 && (
              <div className="mt-6 pt-4 border-t border-border">
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="text-muted-foreground">任务完成率</span>
                  <span className="font-semibold tabular-nums">
                    {Math.round((taskStats.success / taskStats.total) * 100)}%
                  </span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-success rounded-full transition-all duration-500"
                    style={{ width: `${(taskStats.success / taskStats.total) * 100}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Quick Actions - 2 columns */}
          <div className="lg:col-span-2 bg-card rounded-lg border shadow-soft p-6">
            <h2 className="text-lg font-semibold mb-4">快速操作</h2>
            <div className="grid grid-cols-2 gap-3">
              {quickLinks.map((link) => (
                <Link key={link.href} href={link.href}>
                  <div className="group bg-muted rounded-lg hover:bg-accent p-4 transition-colors cursor-pointer">
                    <div className={cn("w-fit p-2 rounded-md mb-3", link.accent)}>
                      <link.icon className="h-4 w-4 text-white" />
                    </div>
                    <p className="text-sm font-medium group-hover:text-accent-foreground">
                      {link.name}
                    </p>
                    <ArrowRight className="h-4 w-4 mt-2 text-muted-foreground group-hover:text-foreground group-hover:translate-x-1 transition-all" />
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Tasks */}
        <div className="bg-card rounded-lg border shadow-soft">
          <div className="flex items-center justify-between p-6 border-b border-border">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold">最近任务</h2>
            </div>
            <Link
              href="/tasks"
              className="flex items-center gap-1 text-sm font-medium text-primary hover:underline"
            >
              查看全部
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          <div className="p-6">
            {isLoading ? (
              <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="flex items-center gap-4">
                    <Skeleton className="h-8 w-16" />
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-4 w-24 ml-auto" />
                  </div>
                ))}
              </div>
            ) : recentTasks.length > 0 ? (
              <div className="space-y-3">
                {recentTasks.map((task, index) => {
                  const config = statusConfig[task.status] || statusConfig.pending;
                  const StatusIcon = config.icon;
                  return (
                    <div
                      key={task.id}
                      className="flex items-center justify-between py-3 border-b border-border last:border-0"
                      style={{ animationDelay: `${index * 50}ms` }}
                    >
                      <div className="flex items-center gap-4">
                        <div className={cn("flex items-center gap-1.5 px-2.5 py-1 rounded-md", config.bg)}>
                          <StatusIcon
                            className={cn(
                              "h-3.5 w-3.5 text-white",
                              task.status === "running" && "animate-spin"
                            )}
                          />
                          <span className="text-xs font-medium text-white">
                            {config.label}
                          </span>
                        </div>
                        <span className="font-medium">
                          {taskTypeLabels[task.task_type] || task.task_type}
                        </span>
                      </div>
                      <div className="flex items-center gap-6">
                        {task.status === "running" && (
                          <div className="w-32">
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="text-muted-foreground">进度</span>
                              <span className="font-medium tabular-nums">{task.progress}%</span>
                            </div>
                            <Progress value={task.progress} className="h-1.5" />
                          </div>
                        )}
                        <span className="text-sm tabular-nums text-muted-foreground min-w-[80px] text-right">
                          {task.records_count.toLocaleString()} 条
                        </span>
                        <span className="text-sm text-muted-foreground min-w-[80px]">
                          {new Date(task.created_at).toLocaleDateString("zh-CN")}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <EmptyState
                icon={ListTodo}
                title="暂无任务记录"
                description="开始创建第一个爬虫任务来采集城市数据"
                action={{
                  label: "创建任务",
                  onClick: () => (window.location.href = "/tasks"),
                  icon: ListTodo,
                }}
              />
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
