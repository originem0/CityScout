"use client";

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
import { Switch } from "@/components/ui/switch";
import { RefreshCw, ExternalLink, AlertCircle, CheckCircle } from "lucide-react";
import { useDataSources, useToggleDataSource } from "@/hooks/use-sources";
import { formatDistanceToNow } from "date-fns";
import { zhCN } from "date-fns/locale";

const typeLabels: Record<string, string> = {
  job: "招聘网站",
  rent: "房产网站",
  forum: "论坛社区",
  public_data: "公开数据",
};

const typeColors: Record<string, string> = {
  job: "bg-blue-100 text-blue-800",
  rent: "bg-green-100 text-green-800",
  forum: "bg-purple-100 text-purple-800",
  public_data: "bg-gray-100 text-gray-800",
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
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">数据源管理</h1>
            <p className="text-slate-500">管理招聘网站、房产网站、论坛等数据源</p>
          </div>
          <Button variant="outline" size="icon" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>
              数据源列表
              {sources && sources.length > 0 && (
                <span className="ml-2 text-sm font-normal text-slate-500">
                  共 {sources.length} 个数据源，
                  {sources.filter((s) => s.enabled).length} 个已启用
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <p className="text-center py-8 text-slate-500">加载中...</p>
            ) : sources && sources.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>数据源</TableHead>
                    <TableHead>类型</TableHead>
                    <TableHead>标识</TableHead>
                    <TableHead>优先级</TableHead>
                    <TableHead>最近成功</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead className="text-right">启用</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sources.map((source) => (
                    <TableRow key={source.id}>
                      <TableCell className="font-medium">
                        {source.name}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="secondary"
                          className={typeColors[source.type] || ""}
                        >
                          {typeLabels[source.type] || source.type}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <code className="text-sm bg-slate-100 px-1.5 py-0.5 rounded">
                          {source.slug}
                        </code>
                      </TableCell>
                      <TableCell>{source.priority}</TableCell>
                      <TableCell>
                        {source.last_success_at ? (
                          <span className="flex items-center gap-1 text-green-600">
                            <CheckCircle className="h-3.5 w-3.5" />
                            {formatDistanceToNow(new Date(source.last_success_at), {
                              addSuffix: true,
                              locale: zhCN,
                            })}
                          </span>
                        ) : (
                          <span className="text-slate-400">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {source.last_error ? (
                          <span
                            className="flex items-center gap-1 text-red-600 cursor-help"
                            title={source.last_error}
                          >
                            <AlertCircle className="h-3.5 w-3.5" />
                            有错误
                          </span>
                        ) : (
                          <span className="text-green-600">正常</span>
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
              <div className="text-center py-12">
                <p className="text-slate-500 mb-2">暂无数据源配置</p>
                <p className="text-sm text-slate-400">
                  数据源将在系统初始化时自动创建
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>数据源说明</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <h4 className="font-medium text-blue-800">招聘网站</h4>
                <p className="text-sm text-slate-600">
                  58同城、Boss直聘等，用于采集岗位信息、薪资数据
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-green-800">房产网站</h4>
                <p className="text-sm text-slate-600">
                  58同城租房、安居客等，用于采集房租价格
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-purple-800">论坛社区</h4>
                <p className="text-sm text-slate-600">
                  V2EX、贴吧、知乎等，用于采集城市真实评价
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-gray-800">公开数据</h4>
                <p className="text-sm text-slate-600">
                  Numbeo、天气网站等，用于采集生活成本、气候数据
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
