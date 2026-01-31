"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { PageHeader } from "@/components/common/page-header";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { FileDown, FileSpreadsheet, FileText, Bot, Copy, Loader2 } from "lucide-react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { toast } from "sonner";

export default function ExportPage() {
  const [forumCityId, setForumCityId] = useState<string>("all");
  const [aiPrompt, setAiPrompt] = useState<string>("");

  const { data: cities } = useQuery({
    queryKey: ["cities"],
    queryFn: () => api.cities.list(),
  });

  const aiReportMutation = useMutation({
    mutationFn: () => api.export.aiReport(),
    onSuccess: (data) => {
      setAiPrompt(data.prompt);
      toast.success(`已生成提示词（覆盖 ${data.city_count} 个城市）`);
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });

  const handleCopyPrompt = () => {
    navigator.clipboard.writeText(aiPrompt);
    toast.success("已复制到剪贴板");
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <PageHeader
          icon={FileDown}
          title="数据导出"
          description="导出分析数据和报告"
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Excel Export */}
          <Card className="transition-shadow hover:shadow-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileSpreadsheet className="h-5 w-5 text-success" />
                城市对比表（CSV）
              </CardTitle>
              <CardDescription>
                导出所有城市的薪资、租金、论坛数据对比表，可用 Excel 打开
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={() => window.open(api.export.cityComparisonCsvUrl(), "_blank")}
              >
                <FileDown className="h-4 w-4 mr-2" />
                下载 CSV
              </Button>
            </CardContent>
          </Card>

          {/* Markdown Export */}
          <Card className="transition-shadow hover:shadow-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-chart-4" />
                论坛评论汇总（Markdown）
              </CardTitle>
              <CardDescription>
                按热度排序导出论坛帖子摘要
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>选择城市</Label>
                <Select value={forumCityId} onValueChange={setForumCityId}>
                  <SelectTrigger>
                    <SelectValue placeholder="全部城市" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">全部城市</SelectItem>
                    {cities?.map((city) => (
                      <SelectItem key={city.id} value={String(city.id)}>
                        {city.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button
                onClick={() =>
                  window.open(
                    api.export.forumSummaryMdUrl(
                      forumCityId !== "all" ? parseInt(forumCityId) : undefined
                    ),
                    "_blank"
                  )
                }
              >
                <FileDown className="h-4 w-4 mr-2" />
                下载 Markdown
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* AI Report */}
        <Card className="transition-shadow hover:shadow-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5 text-primary" />
              AI 分析报告
            </CardTitle>
            <CardDescription>
              基于采集数据生成分析提示词，可用于 ChatGPT / Claude 等 AI 工具进行深度分析
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={() => aiReportMutation.mutate()}
              disabled={aiReportMutation.isPending}
            >
              {aiReportMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Bot className="h-4 w-4 mr-2" />
              )}
              生成分析提示词
            </Button>

            {aiPrompt && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>生成的提示词</Label>
                  <Button variant="outline" size="sm" onClick={handleCopyPrompt}>
                    <Copy className="h-4 w-4 mr-2" />
                    复制
                  </Button>
                </div>
                <Textarea
                  value={aiPrompt}
                  readOnly
                  className="font-mono h-96"
                />
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
