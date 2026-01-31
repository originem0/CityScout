"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  ExternalLink,
  Copy,
  Check,
  Search,
  Briefcase,
  MessageSquare,
  RefreshCw,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { toast } from "sonner";
import type { PlatformSearchGuide } from "@/types";

const platformIcons: Record<string, React.ReactNode> = {
  boss: <Briefcase className="h-5 w-5" />,
  zhihu: <MessageSquare className="h-5 w-5" />,
  weibo: <MessageSquare className="h-5 w-5" />,
  xiaohongshu: <MessageSquare className="h-5 w-5" />,
};

const platformColors: Record<string, string> = {
  boss: "bg-green-100 text-green-800",
  zhihu: "bg-blue-100 text-blue-800",
  weibo: "bg-red-100 text-red-800",
  xiaohongshu: "bg-pink-100 text-pink-800",
};

export default function SearchGuidePage() {
  const [copiedUrl, setCopiedUrl] = useState<string | null>(null);

  const { data: guides, isLoading, refetch } = useQuery({
    queryKey: ["search-guide"],
    queryFn: () => api.import.getGuide(),
  });

  const handleCopyUrl = async (url: string) => {
    try {
      await navigator.clipboard.writeText(url);
      setCopiedUrl(url);
      toast.success("已复制到剪贴板");
      setTimeout(() => setCopiedUrl(null), 2000);
    } catch {
      toast.error("复制失败");
    }
  };

  const handleOpenUrl = (url: string) => {
    window.open(url, "_blank", "noopener,noreferrer");
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">搜索指南</h1>
            <p className="text-slate-500">
              为反爬困难的网站生成搜索链接，方便手动采集数据
            </p>
          </div>
          <Button variant="outline" size="icon" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5" />
              使用说明
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="list-decimal list-inside space-y-2 text-slate-600">
              <li>点击下方链接，在新窗口打开目标网站的搜索页面</li>
              <li>手动浏览搜索结果，复制有价值的内容</li>
              <li>
                前往{" "}
                <a href="/manual-import" className="text-blue-600 underline">
                  数据导入页面
                </a>
                ，将数据导入系统
              </li>
            </ol>
          </CardContent>
        </Card>

        {isLoading ? (
          <div className="text-center py-8 text-slate-500">加载中...</div>
        ) : guides && guides.length > 0 ? (
          <Tabs defaultValue={guides[0].platform}>
            <TabsList className="grid w-full grid-cols-4">
              {guides.map((guide) => (
                <TabsTrigger
                  key={guide.platform}
                  value={guide.platform}
                  className="gap-2"
                >
                  {platformIcons[guide.platform]}
                  {guide.platform_name}
                </TabsTrigger>
              ))}
            </TabsList>

            {guides.map((guide) => (
              <TabsContent key={guide.platform} value={guide.platform}>
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Badge className={platformColors[guide.platform]}>
                        {guide.platform_name}
                      </Badge>
                      {guide.description}
                    </CardTitle>
                    <CardDescription>
                      <div className="mt-2 space-y-1">
                        <p className="font-medium">搜索技巧：</p>
                        <ul className="list-disc list-inside text-sm">
                          {guide.tips.map((tip, i) => (
                            <li key={i}>{tip}</li>
                          ))}
                        </ul>
                      </div>
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {guide.search_urls.length > 0 ? (
                        guide.search_urls.map((item, i) => (
                          <div
                            key={i}
                            className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
                          >
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <Badge variant="outline">{item.city}</Badge>
                                <span className="text-sm text-slate-600">
                                  {item.keyword}
                                </span>
                              </div>
                              <p className="text-xs text-slate-400 truncate mt-1">
                                {item.url}
                              </p>
                            </div>
                            <div className="flex gap-2 ml-4">
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleCopyUrl(item.url)}
                                title="复制链接"
                              >
                                {copiedUrl === item.url ? (
                                  <Check className="h-4 w-4 text-green-600" />
                                ) : (
                                  <Copy className="h-4 w-4" />
                                )}
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleOpenUrl(item.url)}
                                title="打开链接"
                              >
                                <ExternalLink className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        ))
                      ) : (
                        <p className="text-center text-slate-500 py-4">
                          暂无搜索链接，请先添加城市和关键词
                        </p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            ))}
          </Tabs>
        ) : (
          <Card>
            <CardContent className="py-8 text-center text-slate-500">
              暂无搜索指南，请先配置城市和关键词
            </CardContent>
          </Card>
        )}
      </div>
    </AppLayout>
  );
}
