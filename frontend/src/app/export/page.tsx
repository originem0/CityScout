"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout";
import { Button } from "@/components/ui/button";
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
          <div className="bg-card rounded-lg border shadow-soft card-hover">
            <div className="p-6 border-b border-border">
              <div className="flex items-center gap-2 mb-1">
                <div className="bg-success rounded-md p-1.5">
                  <FileSpreadsheet className="h-4 w-4 text-white" />
                </div>
                <h3 className="text-lg font-semibold">城市对比表（CSV）</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                导出所有城市的薪资、租金、论坛数据对比表，可用 Excel 打开
              </p>
            </div>
            <div className="p-6">
              <Button
                onClick={() => window.open(api.export.cityComparisonCsvUrl(), "_blank")}
              >
                <FileDown className="h-4 w-4 mr-2" />
                下载 CSV
              </Button>
            </div>
          </div>

          {/* Markdown Export */}
          <div className="bg-card rounded-lg border shadow-soft card-hover">
            <div className="p-6 border-b border-border">
              <div className="flex items-center gap-2 mb-1">
                <div className="bg-chart-4 rounded-md p-1.5">
                  <FileText className="h-4 w-4 text-white" />
                </div>
                <h3 className="text-lg font-semibold">论坛评论汇总（Markdown）</h3>
              </div>
              <p className="text-sm text-muted-foreground">
                按热度排序导出论坛帖子摘要
              </p>
            </div>
            <div className="p-6 space-y-4">
              <div className="space-y-2">
                <Label className="text-xs font-medium">选择城市</Label>
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
            </div>
          </div>
        </div>

        {/* AI Report */}
        <div className="bg-card rounded-lg border shadow-soft">
          <div className="p-6 border-b border-border">
            <div className="flex items-center gap-2 mb-1">
              <div className="bg-primary rounded-md p-1.5">
                <Bot className="h-4 w-4 text-white" />
              </div>
              <h3 className="text-lg font-semibold">AI 分析报告</h3>
            </div>
            <p className="text-sm text-muted-foreground">
              基于采集数据生成分析提示词，可用于 ChatGPT / Claude 等 AI 工具进行深度分析
            </p>
          </div>
          <div className="p-6 space-y-4">
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
                  <Label className="text-xs font-medium">生成的提示词</Label>
                  <Button variant="outline" size="sm" onClick={handleCopyPrompt}>
                    <Copy className="h-4 w-4 mr-2" />
                    复制
                  </Button>
                </div>
                <Textarea
                  value={aiPrompt}
                  readOnly
                  className="font-mono h-96 bg-muted rounded-lg"
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
