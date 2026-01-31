"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageHeader } from "@/components/common/page-header";
import { Skeleton, SkeletonChart } from "@/components/ui/skeleton";
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
import type { CityComparisonItem, CityScore } from "@/types";

const DIMENSION_OPTIONS = [
  { value: "salary", label: "平均薪资" },
  { value: "rent", label: "平均租金" },
  { value: "ratio", label: "薪租比" },
  { value: "jobs", label: "岗位数量" },
  { value: "forum", label: "讨论热度" },
];

const COLORS = [
  "#3b82f6", "#ef4444", "#22c55e", "#f59e0b", "#8b5cf6",
  "#ec4899", "#06b6d4", "#f97316", "#14b8a6", "#6366f1",
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

  // Chart data for salary comparison
  const salaryChartData = comparison?.comparison
    ?.filter((c: CityComparisonItem) => c.avg_salary)
    .sort((a: CityComparisonItem, b: CityComparisonItem) => (b.avg_salary || 0) - (a.avg_salary || 0))
    .slice(0, 15)
    .map((c: CityComparisonItem) => ({
      name: c.city_name,
      薪资下限: c.avg_salary_min,
      薪资上限: c.avg_salary_max,
    })) || [];

  // Chart data for rent comparison
  const rentChartData = comparison?.comparison
    ?.filter((c: CityComparisonItem) => c.avg_rent)
    .sort((a: CityComparisonItem, b: CityComparisonItem) => (b.avg_rent || 0) - (a.avg_rent || 0))
    .slice(0, 15)
    .map((c: CityComparisonItem) => ({
      name: c.city_name,
      平均租金: c.avg_rent,
    })) || [];

  // Radar data for top 5 scored cities
  const radarData = scores?.scores?.slice(0, 5).map((s: CityScore) => ({
    city: s.city_name,
    薪资: s.salary_score,
    租金: s.rent_score,
    薪租比: s.ratio_score,
    讨论度: s.forum_score,
  })) || [];

  // Transform for radar chart (need subjects as data points)
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
            {/* Salary Chart */}
            {salaryChartData.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>各城市平均薪资对比</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={salaryChartData} margin={{ bottom: 60 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" angle={-45} textAnchor="end" fontSize={12} />
                      <YAxis />
                      <Tooltip formatter={(v) => `${Number(v)?.toLocaleString()}元`} />
                      <Legend />
                      <Bar dataKey="薪资下限" fill="#3b82f6" />
                      <Bar dataKey="薪资上限" fill="#60a5fa" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            )}

            {/* Rent Chart */}
            {rentChartData.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>各城市平均租金对比</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={rentChartData} margin={{ bottom: 60 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" angle={-45} textAnchor="end" fontSize={12} />
                      <YAxis />
                      <Tooltip formatter={(v) => `${Number(v)?.toLocaleString()}元/月`} />
                      <Legend />
                      <Bar dataKey="平均租金" fill="#f59e0b" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            )}

            {/* Comparison Table */}
            {comparison && comparison.comparison.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>城市数据对比表</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>城市</TableHead>
                          <TableHead>等级</TableHead>
                          <TableHead className="text-right">岗位数</TableHead>
                          <TableHead className="text-right">平均薪资</TableHead>
                          <TableHead className="text-right">房源数</TableHead>
                          <TableHead className="text-right">平均租金</TableHead>
                          <TableHead className="text-right">薪租比</TableHead>
                          <TableHead className="text-right">帖子数</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {comparison.comparison.map((c: CityComparisonItem) => (
                          <TableRow key={c.city_id}>
                            <TableCell className="font-medium">{c.city_name}</TableCell>
                            <TableCell>
                              <Badge variant="outline">{c.tier}</Badge>
                            </TableCell>
                            <TableCell className="text-right">{c.job_count}</TableCell>
                            <TableCell className="text-right text-green-600">
                              {c.avg_salary ? `${c.avg_salary.toLocaleString()}` : "-"}
                            </TableCell>
                            <TableCell className="text-right">{c.rent_count}</TableCell>
                            <TableCell className="text-right text-orange-600">
                              {c.avg_rent ? `${c.avg_rent.toLocaleString()}` : "-"}
                            </TableCell>
                            <TableCell className="text-right font-medium">
                              {c.salary_rent_ratio ?? "-"}
                            </TableCell>
                            <TableCell className="text-right">{c.post_count}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            )}

            {compLoading && (
              <div className="space-y-6">
                <SkeletonChart className="h-[400px]" />
                <SkeletonChart className="h-[400px]" />
              </div>
            )}
            {!compLoading && (!comparison || comparison.comparison.length === 0) && (
              <div className="text-center py-12 text-muted-foreground">
                暂无数据，请先采集或导入数据
              </div>
            )}
          </TabsContent>

          {/* Rankings Tab */}
          <TabsContent value="rankings" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <Trophy className="h-5 w-5" />
                    城市排名
                  </CardTitle>
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
                  <CardDescription>
                    按{rankings.label}排名（单位: {rankings.unit}）
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent>
                {rankLoading && (
                  <div className="space-y-2 py-8">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Skeleton key={i} className="h-12 w-full" />
                    ))}
                  </div>
                )}
                {rankings && rankings.rankings.length > 0 && (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-16">排名</TableHead>
                        <TableHead>城市</TableHead>
                        <TableHead>省份</TableHead>
                        <TableHead className="text-right">
                          {rankings.label}
                        </TableHead>
                        {rankings.rankings[0]?.sample_size !== undefined && (
                          <TableHead className="text-right">样本数</TableHead>
                        )}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {rankings.rankings.map((r) => (
                        <TableRow key={r.city_id}>
                          <TableCell>
                            <Badge
                              variant={r.rank <= 3 ? "default" : "outline"}
                              className={
                                r.rank === 1
                                  ? "bg-yellow-500"
                                  : r.rank === 2
                                  ? "bg-gray-400"
                                  : r.rank === 3
                                  ? "bg-amber-600"
                                  : ""
                              }
                            >
                              #{r.rank}
                            </Badge>
                          </TableCell>
                          <TableCell className="font-medium">{r.city_name}</TableCell>
                          <TableCell>{r.province}</TableCell>
                          <TableCell className="text-right font-medium">
                            {r.value.toLocaleString()} {rankings.unit}
                          </TableCell>
                          {r.sample_size !== undefined && (
                            <TableCell className="text-right text-slate-500">
                              {r.sample_size}
                            </TableCell>
                          )}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
                {!rankLoading && (!rankings || rankings.rankings.length === 0) && (
                  <div className="text-center py-8 text-muted-foreground">暂无排名数据</div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Scores Tab */}
          <TabsContent value="scores" className="space-y-6">
            {/* Radar Chart */}
            {radarChartData.length > 0 && scores?.scores && scores.scores.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Top 5 城市雷达图</CardTitle>
                  <CardDescription>各维度得分对比（0-100分）</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={400}>
                    <RadarChart data={radarChartData}>
                      <PolarGrid />
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
                </CardContent>
              </Card>
            )}

            {/* Scores Table */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  综合评分排名
                </CardTitle>
                <CardDescription>
                  权重: 薪资({scores?.weights?.salary || 40}%) 租金({scores?.weights?.rent || 30}%)
                  薪租比({scores?.weights?.ratio || 20}%) 讨论度({scores?.weights?.forum || 10}%)
                </CardDescription>
              </CardHeader>
              <CardContent>
                {scoreLoading && (
                  <div className="space-y-2 py-8">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Skeleton key={i} className="h-12 w-full" />
                    ))}
                  </div>
                )}
                {scores && scores.scores.length > 0 && (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-16">排名</TableHead>
                          <TableHead>城市</TableHead>
                          <TableHead className="text-right">综合分</TableHead>
                          <TableHead className="text-right">薪资分</TableHead>
                          <TableHead className="text-right">租金分</TableHead>
                          <TableHead className="text-right">薪租比</TableHead>
                          <TableHead className="text-right">讨论度</TableHead>
                          <TableHead className="text-right">平均薪资</TableHead>
                          <TableHead className="text-right">平均租金</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {scores.scores.map((s: CityScore) => (
                          <TableRow key={s.city_id}>
                            <TableCell>
                              <Badge
                                variant={s.rank <= 3 ? "default" : "outline"}
                                className={
                                  s.rank === 1
                                    ? "bg-yellow-500"
                                    : s.rank === 2
                                    ? "bg-gray-400"
                                    : s.rank === 3
                                    ? "bg-amber-600"
                                    : ""
                                }
                              >
                                #{s.rank}
                              </Badge>
                            </TableCell>
                            <TableCell className="font-medium">
                              {s.city_name}
                              <span className="text-xs text-slate-400 ml-1">{s.province}</span>
                            </TableCell>
                            <TableCell className="text-right font-bold text-blue-600">
                              {s.composite_score}
                            </TableCell>
                            <TableCell className="text-right">{s.salary_score}</TableCell>
                            <TableCell className="text-right">{s.rent_score}</TableCell>
                            <TableCell className="text-right">{s.ratio_score}</TableCell>
                            <TableCell className="text-right">{s.forum_score}</TableCell>
                            <TableCell className="text-right text-green-600">
                              {s.avg_salary ? `${s.avg_salary.toLocaleString()}` : "-"}
                            </TableCell>
                            <TableCell className="text-right text-orange-600">
                              {s.avg_rent ? `${s.avg_rent.toLocaleString()}` : "-"}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
                {!scoreLoading && (!scores || scores.scores.length === 0) && (
                  <div className="text-center py-8 text-muted-foreground">暂无评分数据</div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  );
}
