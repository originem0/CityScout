"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout";
import { DataTable } from "@/components/ui/data-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/common/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Briefcase, ExternalLink, Building2, MapPin, RefreshCw, TrendingUp, TrendingDown, DollarSign, Hash } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ColumnDef } from "@tanstack/react-table";
import type { JobListItem, Job } from "@/types";

const columns: ColumnDef<JobListItem>[] = [
  {
    accessorKey: "title",
    header: "职位",
    cell: ({ row }) => (
      <div className="max-w-[200px]">
        <div className="font-medium truncate">{row.getValue("title")}</div>
        <div className="text-xs text-muted-foreground">{row.original.company}</div>
      </div>
    ),
  },
  {
    accessorKey: "city_name",
    header: "城市",
    cell: ({ row }) => (
      <Badge variant="outline">{row.getValue("city_name") || "-"}</Badge>
    ),
  },
  {
    accessorKey: "district",
    header: "区域",
  },
  {
    accessorKey: "salary_raw",
    header: "薪资",
    cell: ({ row }) => (
      <span className="text-success font-medium">
        {row.getValue("salary_raw") || "-"}
      </span>
    ),
  },
  {
    accessorKey: "experience",
    header: "经验",
  },
  {
    accessorKey: "education",
    header: "学历",
  },
  {
    accessorKey: "tags",
    header: "标签",
    cell: ({ row }) => {
      const tags = row.getValue("tags") as string | null;
      if (!tags) return "-";
      return (
        <div className="flex flex-wrap gap-1 max-w-[150px]">
          {tags.split(",").slice(0, 2).map((tag, i) => (
            <Badge key={i} variant="secondary" className="text-xs">
              {tag.trim()}
            </Badge>
          ))}
        </div>
      );
    },
  },
  {
    accessorKey: "data_source_name",
    header: "来源",
    cell: ({ row }) => (
      <Badge variant="outline" className="bg-accent">
        {row.getValue("data_source_name") || "-"}
      </Badge>
    ),
  },
  {
    accessorKey: "crawled_at",
    header: "采集时间",
    cell: ({ row }) => {
      const date = new Date(row.getValue("crawled_at"));
      return date.toLocaleDateString("zh-CN");
    },
  },
];

export default function JobsDataPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [cityId, setCityId] = useState<string>("all");
  const [search, setSearch] = useState("");
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  const { data: cities } = useQuery({
    queryKey: ["cities"],
    queryFn: () => api.cities.list(),
  });

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["jobs", page, pageSize, cityId, search],
    queryFn: () =>
      api.jobs.list({
        skip: page * pageSize,
        limit: pageSize,
        city_id: cityId && cityId !== "all" ? parseInt(cityId) : undefined,
        search: search || undefined,
      }),
  });

  const { data: stats } = useQuery({
    queryKey: ["jobs-stats", cityId],
    queryFn: () => api.jobs.stats(cityId ? parseInt(cityId) : undefined),
  });

  const handleViewDetail = async (job: JobListItem) => {
    try {
      const detail = await api.jobs.get(job.id);
      setSelectedJob(detail);
      setDetailOpen(true);
    } catch (e) {
      console.error(e);
    }
  };

  const columnsWithActions: ColumnDef<JobListItem>[] = [
    ...columns,
    {
      id: "actions",
      cell: ({ row }) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => handleViewDetail(row.original)}
        >
          查看
        </Button>
      ),
    },
  ];

  return (
    <AppLayout>
      <div className="space-y-6">
        <PageHeader
          icon={Briefcase}
          title="招聘数据"
          description="浏览已采集的招聘信息"
          actions={
            <Button variant="outline" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              刷新
            </Button>
          }
        />

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
                  <Hash className="h-4 w-4" />
                  总数量
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  平均薪资
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-success">
                  {stats.avg_salary_min && stats.avg_salary_max
                    ? `${Math.round(stats.avg_salary_min)}-${Math.round(stats.avg_salary_max)}`
                    : "-"}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
                  <TrendingDown className="h-4 w-4" />
                  最低薪资
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats.min_salary ? Math.round(stats.min_salary) : "-"}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  最高薪资
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats.max_salary ? Math.round(stats.max_salary) : "-"}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Filters */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-wrap gap-4">
              <div className="w-48">
                <Label>城市</Label>
                <Select value={cityId} onValueChange={setCityId}>
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
              <div className="flex-1 min-w-[200px]">
                <Label>搜索</Label>
                <Input
                  placeholder="搜索职位、公司..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Data Table */}
        <DataTable
          columns={columnsWithActions}
          data={data?.items || []}
          loading={isLoading}
          pageCount={data ? Math.ceil(data.total / pageSize) : 0}
          pageIndex={page}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={(size) => {
            setPageSize(size);
            setPage(0);
          }}
          total={data?.total}
        />

        {/* Detail Sheet */}
        <Sheet open={detailOpen} onOpenChange={setDetailOpen}>
          <SheetContent className="w-[500px] sm:max-w-[500px] overflow-y-auto">
            {selectedJob && (
              <>
                <SheetHeader>
                  <SheetTitle>{selectedJob.title}</SheetTitle>
                  <SheetDescription className="flex items-center gap-2">
                    <Building2 className="h-4 w-4" />
                    {selectedJob.company || "未知公司"}
                  </SheetDescription>
                </SheetHeader>
                <div className="mt-6 space-y-4">
                  <div className="flex flex-wrap gap-2">
                    <Badge className="bg-success/10 text-success border-success/20" variant="outline">
                      {selectedJob.salary_raw || "薪资面议"}
                    </Badge>
                    {selectedJob.experience && (
                      <Badge variant="outline">{selectedJob.experience}</Badge>
                    )}
                    {selectedJob.education && (
                      <Badge variant="outline">{selectedJob.education}</Badge>
                    )}
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <MapPin className="h-4 w-4 text-muted-foreground" />
                      <span>
                        {selectedJob.city_name} {selectedJob.district}
                      </span>
                    </div>
                    {selectedJob.company_type && (
                      <div className="text-sm text-muted-foreground">
                        公司类型: {selectedJob.company_type}
                      </div>
                    )}
                    {selectedJob.company_size && (
                      <div className="text-sm text-muted-foreground">
                        公司规模: {selectedJob.company_size}
                      </div>
                    )}
                  </div>

                  {selectedJob.tags && (
                    <div className="flex flex-wrap gap-1">
                      {selectedJob.tags.split(",").map((tag, i) => (
                        <Badge key={i} variant="secondary">
                          {tag.trim()}
                        </Badge>
                      ))}
                    </div>
                  )}

                  {selectedJob.description && (
                    <div>
                      <h4 className="font-medium mb-2">职位描述</h4>
                      <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                        {selectedJob.description}
                      </p>
                    </div>
                  )}

                  {selectedJob.benefits && (
                    <div>
                      <h4 className="font-medium mb-2">福利待遇</h4>
                      <p className="text-sm text-muted-foreground">
                        {selectedJob.benefits}
                      </p>
                    </div>
                  )}

                  {selectedJob.source_url && (
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={() =>
                        window.open(selectedJob.source_url!, "_blank")
                      }
                    >
                      <ExternalLink className="h-4 w-4 mr-2" />
                      查看原始链接
                    </Button>
                  )}
                </div>
              </>
            )}
          </SheetContent>
        </Sheet>
      </div>
    </AppLayout>
  );
}
