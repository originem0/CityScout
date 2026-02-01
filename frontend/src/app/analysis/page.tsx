"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageHeader } from "@/components/common/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { BarChart3, Trophy, Target, RefreshCw } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";
import { cn } from "@/lib/utils";
import type { CityComparisonItem, CityScore } from "@/types";

const DIMENSION_OPTIONS = [
  { value: "salary", label: "平均薪资" },
  { value: "rent", label: "平均租金" },
  { value: "ratio", label: "薪租比" },
  { value: "jobs", label: "岗位数量" },
  { value: "forum", label: "讨论热度" },
];

const COLORS = [
  "oklch(0.52 0.24 260)",
  "oklch(0.55 0.24 25)",
  "oklch(0.58 0.18 155)",
  "oklch(0.78 0.16 70)",
  "oklch(0.58 0.22 320)",
];

export default function AnalysisPage() {
  const [rankDimension, setRankDimension] = useState("salary");

  const { data: comparison, isLoading: compLoading, refetch: refetchComp } = useQuery({
    queryKey: ["city-comparison"],
    queryFn: () => api.analysis.cityComparison(),
  });

  const { data: rankings, isLoading: rankLoading } = useQuery({
    queryKey: ["rankings", rankDimension],
    queryFn: () => api.analysis.rankings(rankDimension),
  });

  const { data: scores, isLoading: scoreLoading } = useQuery({
    queryKey: ["city-scores"],
    queryFn: () => api.analysis.scores(),
  });

  const salaryChartData = comparison?.comparison
    ?.filter((c: CityComparisonItem) => c.avg_salary)
    .sort((a: CityComparisonItem, b: CityComparisonItem) => (b.avg_salary || 0) - (a.avg_salary || 0))
    .slice(0, 15)
    .map((c: CityComparisonItem) => ({
      name: c.city_name,
      薪资下限: c.avg_salary_min,
      薪资上限: c.avg_salary_max,
    })) || [];

  const rentChartData = comparison?.comparison
    ?.filter((c: CityComparisonItem) => c.avg_rent)
    .sort((a: CityComparisonItem, b: CityComparisonItem) => (b.avg_rent || 0) - (a.avg_rent || 0))
    .slice(0, 15)
    .map((c: CityComparisonItem) => ({
      name: c.city_name,
      平均租金: c.avg_rent,
    })) || [];

  const radarSubjects = ["薪资", "租金", "薪租比", "讨论度"];
  const radarChartData = radarSubjects.map((subject) => {
    const point: Record<string, string | number> = { subject };
    scores?.scores?.slice(0, 5).forEach((s: CityScore) => {
      const map: Record<string, number> = {
        薪资: s.salary_score,
        租金: s.rent_score,
        薪租比: s.ratio_score,
        讨论度: s.forum_score,
      };
      point[s.city_name] = map[subject] || 0;
    });
    return point;
  });

  const getRankBadgeClass = (rank: number) => {
    if (rank === 1) return "bg-chart-3 text-white";
    if (rank === 2) return "bg-muted-foreground text-white";
    if (rank === 3) return "bg-chart-3/70 text-white";
    return "bg-muted text-muted-foreground";
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <PageHeader
          icon={BarChart3}
          title="数据分析"
          description="城市综合对比与排名分析"
          actions={
            <Button variant="outline" onClick={() => refetchComp()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              刷新数据
            </Button>
          }
        />

        <Tabs defaultValue="comparison">
          <TabsList>
            <TabsTrigger value="comparison">城市对比</TabsTrigger>
            <TabsTrigger value="rankings">维度排名</TabsTrigger>
            <TabsTrigger value="scores">综合评分</TabsTrigger>
          </TabsList>

          {/* City Comparison Tab */}
          <TabsContent value="comparison" className="space-y-6">
            {compLoading ? (
              <div className="space-y-6">
                <div className="bg-card rounded-lg border shadow-soft p-6">
                  <Skeleton className="h-8 w-48 mb-4" />
                  <Skeleton className="h-[400px] w-full" />
                </div>
                <div className="bg-card rounded-lg border shadow-soft p-6">
                  <Skeleton className="h-8 w-48 mb-4" />
                  <Skeleton className="h-[400px] w-full" />
                </div>
              </div>
            ) : (
              <>
                {salaryChartData.length > 0 && (
                  <div className="bg-card rounded-lg border shadow-soft p-6">
                    <h3 className="text-lg font-semibold mb-4">各城市平均薪资对比</h3>
                    <ResponsiveContainer width="100%" height={400}>
                      <BarChart data={salaryChartData} margin={{ bottom: 60 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.82 0.01 260)" />
                        <XAxis dataKey="name" angle={-45} textAnchor="end" fontSize={12} />
                        <YAxis />
                        <Tooltip formatter={(v) => `${Number(v)?.toLocaleString()}元`} />
                        <Legend />
                        <Bar dataKey="薪资下限" fill="oklch(0.52 0.24 260)" />
                        <Bar dataKey="薪资上限" fill="oklch(0.65 0.22 260)" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {rentChartData.length > 0 && (
                  <div className="bg-card rounded-lg border shadow-soft p-6">
                    <h3 className="text-lg font-semibold mb-4">各城市平均租金对比</h3>
                    <ResponsiveContainer width="100%" height={400}>
                      <BarChart data={rentChartData} margin={{ bottom: 60 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.82 0.01 260)" />
                        <XAxis dataKey="name" angle={-45} textAnchor="end" fontSize={12} />
                        <YAxis />
                        <Tooltip formatter={(v) => `${Number(v)?.toLocaleString()}元/月`} />
                        <Legend />
                        <Bar dataKey="平均租金" fill="oklch(0.78 0.16 70)" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {comparison && comparison.comparison.length > 0 && (
                  <div className="bg-card rounded-lg border shadow-soft">
                    <div className="p-6 border-b border-border">
                      <h3 className="text-lg font-semibold">城市数据对比表</h3>
                    </div>
                    <div className="p-6 overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow className="hover:bg-transparent">
                            <TableHead className="text-xs font-medium text-muted-foreground">城市</TableHead>
                            <TableHead className="text-xs font-medium text-muted-foreground">等级</TableHead>
                            <TableHead className="text-right text-xs font-medium text-muted-foreground">岗位数</TableHead>
                            <TableHead className="text-right text-xs font-medium text-muted-foreground">平均薪资</TableHead>
                            <TableHead className="text-right text-xs font-medium text-muted-foreground">房源数</TableHead>
                            <TableHead className="text-right text-xs font-medium text-muted-foreground">平均租金</TableHead>
                            <TableHead className="text-right text-xs font-medium text-muted-foreground">薪租比</TableHead>
                            <TableHead className="text-right text-xs font-medium text-muted-foreground">帖子数</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {comparison.comparison.map((c: CityComparisonItem) => (
                            <TableRow key={c.city_id} className="hover:bg-muted/50">
                              <TableCell className="font-medium">{c.city_name}</TableCell>
                              <TableCell>
                                <span className="px-2 py-0.5 text-xs font-medium bg-muted rounded-md">{c.tier}</span>
                              </TableCell>
                              <TableCell className="text-right tabular-nums">{c.job_count}</TableCell>
                              <TableCell className="text-right tabular-nums text-success font-medium">
                                {c.avg_salary ? `${c.avg_salary.toLocaleString()}` : "-"}
                              </TableCell>
                              <TableCell className="text-right tabular-nums">{c.rent_count}</TableCell>
                              <TableCell className="text-right tabular-nums text-chart-3 font-medium">
                                {c.avg_rent ? `${c.avg_rent.toLocaleString()}` : "-"}
                              </TableCell>
                              <TableCell className="text-right tabular-nums font-bold">
                                {c.salary_rent_ratio ?? "-"}
                              </TableCell>
                              <TableCell className="text-right tabular-nums">{c.post_count}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </div>
                )}

                {!compLoading && (!comparison || comparison.comparison.length === 0) && (
                  <div className="bg-card rounded-lg border shadow-soft p-12 text-center text-muted-foreground">
                    暂无数据，请先采集或导入数据
                  </div>
                )}
              </>
            )}
          </TabsContent>

          {/* Rankings Tab */}
          <TabsContent value="rankings" className="space-y-6">
            <div className="bg-card rounded-lg border shadow-soft">
              <div className="flex items-center justify-between p-6 border-b border-border">
                <div className="flex items-center gap-2">
                  <Trophy className="h-5 w-5 text-chart-3" />
                  <h3 className="text-lg font-semibold">城市排名</h3>
                </div>
                <Select value={rankDimension} onValueChange={setRankDimension}>
                  <SelectTrigger className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {DIMENSION_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {rankings && (
                <p className="px-6 pt-4 text-sm text-muted-foreground">
                  按{rankings.label}排名（单位: {rankings.unit}）
                </p>
              )}
              <div className="p-6">
                {rankLoading ? (
                  <div className="space-y-2">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Skeleton key={i} className="h-12 w-full" />
                    ))}
                  </div>
                ) : rankings && rankings.rankings.length > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow className="hover:bg-transparent">
                        <TableHead className="w-16 text-xs font-medium text-muted-foreground">排名</TableHead>
                        <TableHead className="text-xs font-medium text-muted-foreground">城市</TableHead>
                        <TableHead className="text-xs font-medium text-muted-foreground">省份</TableHead>
                        <TableHead className="text-right text-xs font-medium text-muted-foreground">
                          {rankings.label}
                        </TableHead>
                        {rankings.rankings[0]?.sample_size !== undefined && (
                          <TableHead className="text-right text-xs font-medium text-muted-foreground">样本数</TableHead>
                        )}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {rankings.rankings.map((r) => (
                        <TableRow key={r.city_id} className="hover:bg-muted/50">
                          <TableCell>
                            <span className={cn("px-2 py-0.5 text-xs font-medium rounded-md", getRankBadgeClass(r.rank))}>
                              #{r.rank}
                            </span>
                          </TableCell>
                          <TableCell className="font-medium">{r.city_name}</TableCell>
                          <TableCell>{r.province}</TableCell>
                          <TableCell className="text-right tabular-nums font-bold">
                            {r.value.toLocaleString()} {rankings.unit}
                          </TableCell>
                          {r.sample_size !== undefined && (
                            <TableCell className="text-right tabular-nums text-muted-foreground">
                              {r.sample_size}
                            </TableCell>
                          )}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">暂无排名数据</div>
                )}
              </div>
            </div>
          </TabsContent>

          {/* Scores Tab */}
          <TabsContent value="scores" className="space-y-6">
            {radarChartData.length > 0 && scores?.scores && scores.scores.length > 0 && (
              <div className="bg-card rounded-lg border shadow-soft p-6">
                <h3 className="text-lg font-semibold mb-1">Top 5 城市雷达图</h3>
                <p className="text-sm text-muted-foreground mb-4">各维度得分对比（0-100分）</p>
                <ResponsiveContainer width="100%" height={400}>
                  <RadarChart data={radarChartData}>
                    <PolarGrid stroke="oklch(0.82 0.01 260)" />
                    <PolarAngleAxis dataKey="subject" />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} />
                    {scores.scores.slice(0, 5).map((s: CityScore, i: number) => (
                      <Radar
                        key={s.city_id}
                        name={s.city_name}
                        dataKey={s.city_name}
                        stroke={COLORS[i]}
                        fill={COLORS[i]}
                        fillOpacity={0.1}
                      />
                    ))}
                    <Legend />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            )}

            <div className="bg-card rounded-lg border shadow-soft">
              <div className="p-6 border-b border-border">
                <div className="flex items-center gap-2 mb-1">
                  <Target className="h-5 w-5 text-primary" />
                  <h3 className="text-lg font-semibold">综合评分排名</h3>
                </div>
                <p className="text-sm text-muted-foreground">
                  权重: 薪资({scores?.weights?.salary || 40}%) 租金({scores?.weights?.rent || 30}%)
                  薪租比({scores?.weights?.ratio || 20}%) 讨论度({scores?.weights?.forum || 10}%)
                </p>
              </div>
              <div className="p-6">
                {scoreLoading ? (
                  <div className="space-y-2">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Skeleton key={i} className="h-12 w-full" />
                    ))}
                  </div>
                ) : scores && scores.scores.length > 0 ? (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="hover:bg-transparent">
                          <TableHead className="w-16 text-xs font-medium text-muted-foreground">排名</TableHead>
                          <TableHead className="text-xs font-medium text-muted-foreground">城市</TableHead>
                          <TableHead className="text-right text-xs font-medium text-muted-foreground">综合分</TableHead>
                          <TableHead className="text-right text-xs font-medium text-muted-foreground">薪资分</TableHead>
                          <TableHead className="text-right text-xs font-medium text-muted-foreground">租金分</TableHead>
                          <TableHead className="text-right text-xs font-medium text-muted-foreground">薪租比</TableHead>
                          <TableHead className="text-right text-xs font-medium text-muted-foreground">讨论度</TableHead>
                          <TableHead className="text-right text-xs font-medium text-muted-foreground">平均薪资</TableHead>
                          <TableHead className="text-right text-xs font-medium text-muted-foreground">平均租金</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {scores.scores.map((s: CityScore) => (
                          <TableRow key={s.city_id} className="hover:bg-muted/50">
                            <TableCell>
                              <span className={cn("px-2 py-0.5 text-xs font-bold", getRankBadgeClass(s.rank))}>
                                #{s.rank}
                              </span>
                            </TableCell>
                            <TableCell className="font-medium">
                              {s.city_name}
                              <span className="text-xs text-muted-foreground ml-1">{s.province}</span>
                            </TableCell>
                            <TableCell className="text-right tabular-nums font-bold text-primary">
                              {s.composite_score}
                            </TableCell>
                            <TableCell className="text-right tabular-nums">{s.salary_score}</TableCell>
                            <TableCell className="text-right tabular-nums">{s.rent_score}</TableCell>
                            <TableCell className="text-right tabular-nums">{s.ratio_score}</TableCell>
                            <TableCell className="text-right tabular-nums">{s.forum_score}</TableCell>
                            <TableCell className="text-right tabular-nums text-success">
                              {s.avg_salary ? `${s.avg_salary.toLocaleString()}` : "-"}
                            </TableCell>
                            <TableCell className="text-right tabular-nums text-chart-3">
                              {s.avg_rent ? `${s.avg_rent.toLocaleString()}` : "-"}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">暂无评分数据</div>
                )}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  );
}
