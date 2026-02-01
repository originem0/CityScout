"use client";

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
import { Switch } from "@/components/ui/switch";
import { PageHeader } from "@/components/common/page-header";
import { EmptyState } from "@/components/common/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { RefreshCw, Database, AlertCircle, CheckCircle } from "lucide-react";
import { useDataSources, useToggleDataSource } from "@/hooks/use-sources";
import { formatDistanceToNow } from "date-fns";
import { zhCN } from "date-fns/locale";
import { cn } from "@/lib/utils";

const typeLabels: Record<string, string> = {
  job: "招聘网站",
  rent: "房产网站",
  forum: "论坛社区",
  public_data: "公开数据",
};

const typeColors: Record<string, string> = {
  job: "bg-primary",
  rent: "bg-success",
  forum: "bg-chart-4",
  public_data: "bg-muted-foreground",
};

export default function SourcesPage() {
  const { data: sources, isLoading, refetch } = useDataSources();
  const toggleSource = useToggleDataSource();

  const handleToggle = async (id: number) => {
    await toggleSource.mutateAsync(id);
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <PageHeader
          icon={Database}
          title="数据源管理"
          description="管理招聘网站、房产网站、论坛等数据源"
          actions={
            <Button variant="outline" size="icon" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          }
        />

        <div className="bg-card rounded-lg border shadow-soft">
          <div className="flex items-center justify-between p-6 border-b border-border">
            <h2 className="text-lg font-semibold">数据源列表</h2>
            {sources && sources.length > 0 && (
              <span className="text-sm text-muted-foreground">
                共 <span className="font-bold tabular-nums">{sources.length}</span> 个数据源，
                <span className="font-bold tabular-nums text-success">{sources.filter((s) => s.enabled).length}</span> 个已启用
              </span>
            )}
          </div>
          <div className="p-6">
            {isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-4 py-3">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-6 w-20" />
                    <Skeleton className="h-4 w-16" />
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-6 w-10 ml-auto" />
                  </div>
                ))}
              </div>
            ) : sources && sources.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="text-xs font-medium text-muted-foreground">数据源</TableHead>
                    <TableHead className="text-xs font-medium text-muted-foreground">类型</TableHead>
                    <TableHead className="text-xs font-medium text-muted-foreground">标识</TableHead>
                    <TableHead className="text-xs font-medium text-muted-foreground">优先级</TableHead>
                    <TableHead className="text-xs font-medium text-muted-foreground">最近成功</TableHead>
                    <TableHead className="text-xs font-medium text-muted-foreground">状态</TableHead>
                    <TableHead className="text-right text-xs font-medium text-muted-foreground">启用</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sources.map((source) => (
                    <TableRow key={source.id} className="hover:bg-muted/50">
                      <TableCell className="font-medium">
                        {source.name}
                      </TableCell>
                      <TableCell>
                        <span
                          className={cn(
                            "inline-flex items-center px-2 py-0.5 text-xs font-medium text-white rounded-md",
                            typeColors[source.type] || "bg-muted-foreground"
                          )}
                        >
                          {typeLabels[source.type] || source.type}
                        </span>
                      </TableCell>
                      <TableCell>
                        <code className="text-sm bg-muted px-1.5 py-0.5 font-mono">
                          {source.slug}
                        </code>
                      </TableCell>
                      <TableCell className="tabular-nums">{source.priority}</TableCell>
                      <TableCell>
                        {source.last_success_at ? (
                          <span className="flex items-center gap-1.5 text-success text-sm">
                            <CheckCircle className="h-3.5 w-3.5" />
                            {formatDistanceToNow(new Date(source.last_success_at), {
                              addSuffix: true,
                              locale: zhCN,
                            })}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {source.last_error ? (
                          <span
                            className="flex items-center gap-1.5 text-destructive text-sm cursor-help"
                            title={source.last_error}
                          >
                            <AlertCircle className="h-3.5 w-3.5" />
                            有错误
                          </span>
                        ) : (
                          <span className="flex items-center gap-1.5 text-success text-sm">
                            <CheckCircle className="h-3.5 w-3.5" />
                            正常
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <Switch
                          checked={source.enabled}
                          onCheckedChange={() => handleToggle(source.id)}
                          disabled={toggleSource.isPending}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <EmptyState
                icon={Database}
                title="暂无数据源配置"
                description="数据源将在系统初始化时自动创建"
              />
            )}
          </div>
        </div>

        {/* Data Source Info */}
        <div className="bg-card rounded-lg border shadow-soft p-6">
          <h3 className="text-lg font-semibold mb-4">数据源说明</h3>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="bg-muted rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-3 h-3 rounded-sm bg-primary" />
                <h4 className="font-medium text-sm">招聘网站</h4>
              </div>
              <p className="text-sm text-muted-foreground">
                58同城、Boss直聘等，用于采集岗位信息、薪资数据
              </p>
            </div>
            <div className="bg-muted rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-3 h-3 rounded-sm bg-success" />
                <h4 className="font-medium text-sm">房产网站</h4>
              </div>
              <p className="text-sm text-muted-foreground">
                58同城租房、安居客等，用于采集房租价格
              </p>
            </div>
            <div className="bg-muted rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-3 h-3 rounded-sm bg-chart-4" />
                <h4 className="font-medium text-sm">论坛社区</h4>
              </div>
              <p className="text-sm text-muted-foreground">
                V2EX、贴吧、知乎等，用于采集城市真实评价
              </p>
            </div>
            <div className="bg-muted rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-3 h-3 rounded-sm bg-muted-foreground" />
                <h4 className="font-medium text-sm">公开数据</h4>
              </div>
              <p className="text-sm text-muted-foreground">
                Numbeo、天气网站等，用于采集生活成本、气候数据
              </p>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
