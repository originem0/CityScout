"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageHeader } from "@/components/common/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { Settings, Bot, Shield, Save, Loader2, Trash2, Plus, TestTube } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface CrawlerSettings {
  request_interval: number;
  page_timeout: number;
  max_retries: number;
  max_pages: number;
  user_agent_rotation: boolean;
}

interface ProxySettings {
  enabled: boolean;
  list: string[];
  rotation: boolean;
}

interface SystemSettings {
  crawler: CrawlerSettings;
  proxy: ProxySettings;
}

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [newProxy, setNewProxy] = useState("");

  const { data: settings, isLoading } = useQuery<SystemSettings>({
    queryKey: ["settings"],
    queryFn: async () => {
      const res = await fetch(`${API_BASE_URL}/api/v1/settings`);
      if (!res.ok) throw new Error("Failed to fetch settings");
      return res.json();
    },
  });

  const [crawlerForm, setCrawlerForm] = useState<CrawlerSettings | null>(null);
  const [proxyForm, setProxyForm] = useState<ProxySettings | null>(null);

  // Initialize forms when data loads
  if (settings && !crawlerForm) {
    setCrawlerForm(settings.crawler);
  }
  if (settings && !proxyForm) {
    setProxyForm(settings.proxy);
  }

  const saveCrawlerMutation = useMutation({
    mutationFn: async (data: CrawlerSettings) => {
      const res = await fetch(`${API_BASE_URL}/api/v1/settings/crawler`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error("Failed to save");
      return res.json();
    },
    onSuccess: () => {
      toast.success("爬虫配置已保存");
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
    onError: () => {
      toast.error("保存失败");
    },
  });

  const saveProxyMutation = useMutation({
    mutationFn: async (data: ProxySettings) => {
      const res = await fetch(`${API_BASE_URL}/api/v1/settings/proxy`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error("Failed to save");
      return res.json();
    },
    onSuccess: () => {
      toast.success("代理配置已保存");
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
    onError: () => {
      toast.error("保存失败");
    },
  });

  const testProxyMutation = useMutation({
    mutationFn: async (proxyUrl: string) => {
      const res = await fetch(
        `${API_BASE_URL}/api/v1/settings/proxy/test?proxy_url=${encodeURIComponent(proxyUrl)}`,
        { method: "POST" }
      );
      return res.json();
    },
    onSuccess: (data) => {
      if (data.success) {
        toast.success(`代理可用，IP: ${data.ip}`);
      } else {
        toast.error(`代理不可用: ${data.error}`);
      }
    },
  });

  const handleAddProxy = () => {
    if (!newProxy.trim() || !proxyForm) return;
    if (proxyForm.list.includes(newProxy.trim())) {
      toast.error("代理已存在");
      return;
    }
    setProxyForm({
      ...proxyForm,
      list: [...proxyForm.list, newProxy.trim()],
    });
    setNewProxy("");
  };

  const handleRemoveProxy = (index: number) => {
    if (!proxyForm) return;
    const newList = [...proxyForm.list];
    newList.splice(index, 1);
    setProxyForm({ ...proxyForm, list: newList });
  };

  if (isLoading) {
    return (
      <AppLayout>
        <div className="space-y-6">
          <PageHeader
            icon={Settings}
            title="系统设置"
            description="配置爬虫参数和代理设置"
          />
          <div className="space-y-4">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-64 w-full" />
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <PageHeader
          icon={Settings}
          title="系统设置"
          description="配置爬虫参数和代理设置"
        />

        <Tabs defaultValue="crawler">
          <TabsList>
            <TabsTrigger value="crawler" className="gap-2">
              <Bot className="h-4 w-4" />
              爬虫配置
            </TabsTrigger>
            <TabsTrigger value="proxy" className="gap-2">
              <Shield className="h-4 w-4" />
              代理配置
            </TabsTrigger>
          </TabsList>

          {/* Crawler Settings */}
          <TabsContent value="crawler">
            <Card>
              <CardHeader>
                <CardTitle>爬虫配置</CardTitle>
                <CardDescription>设置爬虫行为参数</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {crawlerForm && (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <Label>请求间隔（秒）</Label>
                        <Input
                          type="number"
                          step="0.1"
                          min="0.5"
                          value={crawlerForm.request_interval}
                          onChange={(e) =>
                            setCrawlerForm({
                              ...crawlerForm,
                              request_interval: parseFloat(e.target.value) || 2,
                            })
                          }
                        />
                        <p className="text-xs text-muted-foreground">
                          每次请求之间的等待时间，建议不低于 1 秒
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Label>页面超时（毫秒）</Label>
                        <Input
                          type="number"
                          step="1000"
                          min="5000"
                          value={crawlerForm.page_timeout}
                          onChange={(e) =>
                            setCrawlerForm({
                              ...crawlerForm,
                              page_timeout: parseInt(e.target.value) || 30000,
                            })
                          }
                        />
                        <p className="text-xs text-muted-foreground">
                          页面加载超时时间
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Label>最大重试次数</Label>
                        <Input
                          type="number"
                          min="1"
                          max="10"
                          value={crawlerForm.max_retries}
                          onChange={(e) =>
                            setCrawlerForm({
                              ...crawlerForm,
                              max_retries: parseInt(e.target.value) || 3,
                            })
                          }
                        />
                        <p className="text-xs text-muted-foreground">
                          请求失败后的重试次数
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Label>最大采集页数</Label>
                        <Input
                          type="number"
                          min="1"
                          max="100"
                          value={crawlerForm.max_pages}
                          onChange={(e) =>
                            setCrawlerForm({
                              ...crawlerForm,
                              max_pages: parseInt(e.target.value) || 10,
                            })
                          }
                        />
                        <p className="text-xs text-muted-foreground">
                          每个任务最多采集的页数
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center justify-between border-t pt-4">
                      <div className="space-y-0.5">
                        <Label>User-Agent 轮换</Label>
                        <p className="text-xs text-muted-foreground">
                          自动轮换浏览器标识，降低被检测风险
                        </p>
                      </div>
                      <Switch
                        checked={crawlerForm.user_agent_rotation}
                        onCheckedChange={(checked) =>
                          setCrawlerForm({
                            ...crawlerForm,
                            user_agent_rotation: checked,
                          })
                        }
                      />
                    </div>

                    <div className="flex justify-end">
                      <Button
                        onClick={() => saveCrawlerMutation.mutate(crawlerForm)}
                        disabled={saveCrawlerMutation.isPending}
                      >
                        {saveCrawlerMutation.isPending ? (
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        ) : (
                          <Save className="h-4 w-4 mr-2" />
                        )}
                        保存配置
                      </Button>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Proxy Settings */}
          <TabsContent value="proxy">
            <Card>
              <CardHeader>
                <CardTitle>代理配置</CardTitle>
                <CardDescription>配置代理服务器以避免 IP 被封</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {proxyForm && (
                  <>
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>启用代理</Label>
                        <p className="text-xs text-muted-foreground">
                          开启后爬虫将通过代理服务器请求
                        </p>
                      </div>
                      <Switch
                        checked={proxyForm.enabled}
                        onCheckedChange={(checked) =>
                          setProxyForm({ ...proxyForm, enabled: checked })
                        }
                      />
                    </div>

                    <div className="flex items-center justify-between border-t pt-4">
                      <div className="space-y-0.5">
                        <Label>代理轮换</Label>
                        <p className="text-xs text-muted-foreground">
                          自动轮换使用代理列表中的代理
                        </p>
                      </div>
                      <Switch
                        checked={proxyForm.rotation}
                        onCheckedChange={(checked) =>
                          setProxyForm({ ...proxyForm, rotation: checked })
                        }
                      />
                    </div>

                    <div className="border-t pt-4 space-y-4">
                      <Label>代理列表</Label>
                      <div className="flex gap-2">
                        <Input
                          placeholder="http://user:pass@host:port"
                          value={newProxy}
                          onChange={(e) => setNewProxy(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") handleAddProxy();
                          }}
                        />
                        <Button variant="outline" onClick={handleAddProxy}>
                          <Plus className="h-4 w-4" />
                        </Button>
                      </div>

                      {proxyForm.list.length > 0 ? (
                        <div className="space-y-2">
                          {proxyForm.list.map((proxy, index) => (
                            <div
                              key={index}
                              className="flex items-center justify-between bg-slate-50 rounded-lg px-3 py-2"
                            >
                              <code className="text-sm">{proxy}</code>
                              <div className="flex gap-2">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => testProxyMutation.mutate(proxy)}
                                  disabled={testProxyMutation.isPending}
                                >
                                  <TestTube className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleRemoveProxy(index)}
                                >
                                  <Trash2 className="h-4 w-4 text-red-500" />
                                </Button>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-muted-foreground text-center py-4">
                          暂无代理，请添加代理服务器地址
                        </p>
                      )}
                    </div>

                    <div className="flex justify-end border-t pt-4">
                      <Button
                        onClick={() => saveProxyMutation.mutate(proxyForm)}
                        disabled={saveProxyMutation.isPending}
                      >
                        {saveProxyMutation.isPending ? (
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        ) : (
                          <Save className="h-4 w-4 mr-2" />
                        )}
                        保存配置
                      </Button>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  );
}
