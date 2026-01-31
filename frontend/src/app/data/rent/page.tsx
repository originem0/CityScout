"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout";
import { DataTable } from "@/components/ui/data-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { Home, ExternalLink, MapPin, Train, RefreshCw } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ColumnDef } from "@tanstack/react-table";
import type { RentListItem, Rent } from "@/types";

const columns: ColumnDef<RentListItem>[] = [
  {
    accessorKey: "title",
    header: "标题",
    cell: ({ row }) => (
      <div className="max-w-[200px]">
        <div className="font-medium truncate">{row.getValue("title")}</div>
        <div className="text-xs text-slate-500">{row.original.neighborhood}</div>
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
    accessorKey: "property_type",
    header: "类型",
    cell: ({ row }) => {
      const type = row.getValue("property_type") as string;
      return type ? (
        <Badge
          variant="outline"
          className={
            type === "整租"
              ? "bg-blue-50 text-blue-700"
              : type === "合租"
              ? "bg-orange-50 text-orange-700"
              : "bg-purple-50 text-purple-700"
          }
        >
          {type}
        </Badge>
      ) : (
        "-"
      );
    },
  },
  {
    accessorKey: "price_raw",
    header: "价格",
    cell: ({ row }) => (
      <span className="text-orange-600 font-medium">
        {row.getValue("price_raw") || "-"}
      </span>
    ),
  },
  {
    accessorKey: "area",
    header: "面积",
    cell: ({ row }) => {
      const area = row.getValue("area") as number | null;
      return area ? `${area}㎡` : "-";
    },
  },
  {
    accessorKey: "layout",
    header: "户型",
  },
  {
    accessorKey: "subway_info",
    header: "地铁",
    cell: ({ row }) => {
      const subway = row.getValue("subway_info") as string | null;
      return subway ? (
        <div className="max-w-[100px] truncate text-xs" title={subway}>
          {subway}
        </div>
      ) : (
        "-"
      );
    },
  },
  {
    accessorKey: "data_source_name",
    header: "来源",
    cell: ({ row }) => (
      <Badge variant="outline" className="bg-blue-50">
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

export default function RentDataPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [cityId, setCityId] = useState<string>("all");
  const [propertyType, setPropertyType] = useState<string>("all");
  const [search, setSearch] = useState("");
  const [selectedRent, setSelectedRent] = useState<Rent | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  const { data: cities } = useQuery({
    queryKey: ["cities"],
    queryFn: () => api.cities.list(),
  });

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["rent", page, pageSize, cityId, propertyType, search],
    queryFn: () =>
      api.rent.list({
        skip: page * pageSize,
        limit: pageSize,
        city_id: cityId && cityId !== "all" ? parseInt(cityId) : undefined,
        property_type: propertyType && propertyType !== "all" ? propertyType : undefined,
        search: search || undefined,
      }),
  });

  const { data: stats } = useQuery({
    queryKey: ["rent-stats", cityId],
    queryFn: () => api.rent.stats(cityId && cityId !== "all" ? parseInt(cityId) : undefined),
  });

  const handleViewDetail = async (rent: RentListItem) => {
    try {
      const detail = await api.rent.get(rent.id);
      setSelectedRent(detail);
      setDetailOpen(true);
    } catch (e) {
      console.error(e);
    }
  };

  const columnsWithActions: ColumnDef<RentListItem>[] = [
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
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Home className="h-8 w-8" />
              租房数据
            </h1>
            <p className="text-slate-500">浏览已采集的租房信息</p>
          </div>
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新
          </Button>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-slate-500">总数量</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-slate-500">平均价格</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-orange-600">
                  {stats.avg_price ? `${Math.round(stats.avg_price)}元` : "-"}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-slate-500">价格范围</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats.min_price && stats.max_price
                    ? `${Math.round(stats.min_price)}-${Math.round(stats.max_price)}`
                    : "-"}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-slate-500">平均面积</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats.avg_area ? `${Math.round(stats.avg_area)}㎡` : "-"}
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
              <div className="w-32">
                <Label>类型</Label>
                <Select value={propertyType} onValueChange={setPropertyType}>
                  <SelectTrigger>
                    <SelectValue placeholder="全部" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">全部</SelectItem>
                    <SelectItem value="整租">整租</SelectItem>
                    <SelectItem value="合租">合租</SelectItem>
                    <SelectItem value="公寓">公寓</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex-1 min-w-[200px]">
                <Label>搜索</Label>
                <Input
                  placeholder="搜索标题、小区..."
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
            {selectedRent && (
              <>
                <SheetHeader>
                  <SheetTitle>{selectedRent.title}</SheetTitle>
                  <SheetDescription className="flex items-center gap-2">
                    <MapPin className="h-4 w-4" />
                    {selectedRent.neighborhood || selectedRent.district}
                  </SheetDescription>
                </SheetHeader>
                <div className="mt-6 space-y-4">
                  <div className="flex flex-wrap gap-2">
                    <Badge className="bg-orange-100 text-orange-800 text-lg px-3 py-1">
                      {selectedRent.price_raw || "价格面议"}
                    </Badge>
                    {selectedRent.property_type && (
                      <Badge variant="outline">{selectedRent.property_type}</Badge>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-slate-500">面积:</span>{" "}
                      {selectedRent.area ? `${selectedRent.area}㎡` : "-"}
                    </div>
                    <div>
                      <span className="text-slate-500">户型:</span>{" "}
                      {selectedRent.layout || "-"}
                    </div>
                    <div>
                      <span className="text-slate-500">楼层:</span>{" "}
                      {selectedRent.floor || "-"}
                    </div>
                    <div>
                      <span className="text-slate-500">朝向:</span>{" "}
                      {selectedRent.orientation || "-"}
                    </div>
                    <div>
                      <span className="text-slate-500">装修:</span>{" "}
                      {selectedRent.decoration || "-"}
                    </div>
                    <div>
                      <span className="text-slate-500">付款:</span>{" "}
                      {selectedRent.payment_type || "-"}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <MapPin className="h-4 w-4 text-slate-400" />
                      <span>
                        {selectedRent.city_name} {selectedRent.district}{" "}
                        {selectedRent.address}
                      </span>
                    </div>
                    {selectedRent.subway_info && (
                      <div className="flex items-center gap-2 text-sm">
                        <Train className="h-4 w-4 text-slate-400" />
                        <span>{selectedRent.subway_info}</span>
                      </div>
                    )}
                  </div>

                  {selectedRent.facilities && (
                    <div>
                      <h4 className="font-medium mb-2">配套设施</h4>
                      <div className="flex flex-wrap gap-1">
                        {selectedRent.facilities.split(",").map((f, i) => (
                          <Badge key={i} variant="secondary">
                            {f.trim()}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedRent.description && (
                    <div>
                      <h4 className="font-medium mb-2">房源描述</h4>
                      <p className="text-sm text-slate-600 whitespace-pre-wrap">
                        {selectedRent.description}
                      </p>
                    </div>
                  )}

                  {selectedRent.agent_name && (
                    <div className="text-sm">
                      <span className="text-slate-500">联系人:</span>{" "}
                      {selectedRent.agent_name}
                      {selectedRent.agent_phone && ` (${selectedRent.agent_phone})`}
                    </div>
                  )}

                  {selectedRent.source_url && (
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={() =>
                        window.open(selectedRent.source_url!, "_blank")
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
