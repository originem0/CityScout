"use client";

import { AppLayout } from "@/components/layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/common/page-header";
import { EmptyState } from "@/components/common/empty-state";
import { Skeleton, SkeletonCard } from "@/components/ui/skeleton";
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
  LayoutDashboard,
  TrendingUp,
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
  job_crawl: "招聘爬虫",
  rent_crawl: "租房爬虫",
  forum_crawl: "论坛爬虫",
  public_data: "公共数据",
};

const statusConfig: Record<
  string,
  { label: string; color: string; icon: typeof Clock }
> = {
  pending: { label: "等待中", color: "bg-warning/10 text-warning-foreground border-warning/20", icon: Clock },
  running: { label: "运行中", color: "bg-primary/10 text-primary border-primary/20", icon: Loader2 },
  success: { label: "成功", color: "bg-success/10 text-success border-success/20", icon: CheckCircle2 },
  failed: { label: "失败", color: "bg-destructive/10 text-destructive border-destructive/20", icon: XCircle },
  cancelled: { label: "已取消", color: "bg-muted text-muted-foreground border-border", icon: XCircle },
};

const quickLinks = [
  { name: "创建爬虫任务", href: "/tasks", icon: ListTodo, color: "text-primary" },
  { name: "手动导入数据", href: "/manual-import", icon: Upload, color: "text-chart-4" },
  { name: "查看数据分析", href: "/analysis", icon: BarChart3, color: "text-success" },
  { name: "导出报告", href: "/export", icon: FileDown, color: "text-chart-3" },
];

interface StatCardProps {
  title: string;
  value: number | string;
  description: string;
  icon: typeof MapPin;
  accentColor: string;
  isLoading?: boolean;
}

function StatCard({
  title,
  value,
  description,
  icon: Icon,
  accentColor,
  isLoading,
}: StatCardProps) {
  return (
    <Card className="relative overflow-hidden transition-shadow hover:shadow-md">
      <div className={cn("absolute left-0 top-0 bottom-0 w-1", accentColor)} />
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className={cn("h-4 w-4", accentColor.replace("bg-", "text-"))} />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-8 w-20" />
        ) : (
          <div className="text-2xl font-bold">{value}</div>
        )}
        <p className="text-xs text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
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
      <div className="space-y-6">
        <PageHeader
          icon={LayoutDashboard}
          title="仪表盘"
          description="CityScout 城市分析系统概览"
        />

        {/* Data Overview Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="目标城市"
            value={counts?.cities ?? "-"}
            description="已配置的目标城市"
            icon={MapPin}
            accentColor="bg-primary"
            isLoading={isLoading}
          />
          <StatCard
            title="招聘岗位"
            value={counts?.jobs?.toLocaleString() ?? "-"}
            description="已采集的招聘数据"
            icon={Briefcase}
            accentColor="bg-chart-1"
            isLoading={isLoading}
          />
          <StatCard
            title="房源信息"
            value={counts?.rent?.toLocaleString() ?? "-"}
            description="已采集的租房数据"
            icon={Home}
            accentColor="bg-chart-3"
            isLoading={isLoading}
          />
          <StatCard
            title="论坛帖子"
            value={counts?.forum?.toLocaleString() ?? "-"}
            description="已采集的论坛数据"
            icon={MessageSquare}
            accentColor="bg-chart-2"
            isLoading={isLoading}
          />
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {/* Task Stats */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ListTodo className="h-5 w-5 text-primary" />
                爬虫任务统计
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-3">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-4 w-1/2" />
                </div>
              ) : taskStats ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-warning" />
                      <span className="text-sm">等待中: {taskStats.pending}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-primary" />
                      <span className="text-sm">运行中: {taskStats.running}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-success" />
                      <span className="text-sm">成功: {taskStats.success}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-destructive" />
                      <span className="text-sm">失败: {taskStats.failed}</span>
                    </div>
                  </div>
                  <div className="pt-2 border-t">
                    <div className="flex items-center justify-between text-sm text-muted-foreground">
                      <span>总任务数: {taskStats.total}</span>
                      <span className="flex items-center gap-1">
                        <TrendingUp className="h-4 w-4" />
                        总数据量: {counts?.total_data?.toLocaleString() ?? 0}
                      </span>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">暂无数据</p>
              )}
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>快速操作</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3">
                {quickLinks.map((link) => (
                  <Link key={link.href} href={link.href}>
                    <Button
                      variant="outline"
                      className="w-full justify-start gap-2 h-auto py-3 hover:shadow-sm transition-shadow"
                    >
                      <link.icon className={cn("h-4 w-4", link.color)} />
                      <span className="text-sm">{link.name}</span>
                    </Button>
                  </Link>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Tasks */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>最近任务</CardTitle>
            <Link href="/tasks">
              <Button variant="ghost" size="sm">
                查看全部 <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-4 py-2">
                    <Skeleton className="h-6 w-16" />
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-2 w-32 ml-auto" />
                  </div>
                ))}
              </div>
            ) : recentTasks.length > 0 ? (
              <div className="space-y-3">
                {recentTasks.map((task) => {
                  const config = statusConfig[task.status] || statusConfig.pending;
                  const StatusIcon = config.icon;
                  return (
                    <div
                      key={task.id}
                      className="flex items-center justify-between py-2 border-b last:border-0"
                    >
                      <div className="flex items-center gap-3">
                        <Badge
                          variant="outline"
                          className={cn("gap-1", config.color)}
                        >
                          <StatusIcon
                            className={cn(
                              "h-3 w-3",
                              task.status === "running" && "animate-spin"
                            )}
                          />
                          {config.label}
                        </Badge>
                        <span className="text-sm font-medium">
                          {taskTypeLabels[task.task_type] || task.task_type}
                        </span>
                      </div>
                      <div className="flex items-center gap-4">
                        {task.status === "running" && (
                          <div className="w-24">
                            <Progress value={task.progress} className="h-1.5" />
                          </div>
                        )}
                        <span className="text-sm text-muted-foreground">
                          {task.records_count} 条数据
                        </span>
                        <span className="text-sm text-muted-foreground">
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
                  label: "创建爬虫任务",
                  onClick: () => (window.location.href = "/tasks"),
                  icon: ListTodo,
                }}
              />
            )}
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
