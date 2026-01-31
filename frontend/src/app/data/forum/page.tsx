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
import {
  MessageSquare,
  ExternalLink,
  ThumbsUp,
  MessageCircle,
  User,
  RefreshCw,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ColumnDef } from "@tanstack/react-table";
import type { ForumPostListItem, ForumPost } from "@/types";

const columns: ColumnDef<ForumPostListItem>[] = [
  {
    accessorKey: "title",
    header: "标题",
    cell: ({ row }) => {
      const title = row.getValue("title") as string | null;
      const content = row.original.content;
      return (
        <div className="max-w-[250px]">
          <div className="font-medium truncate">
            {title || content.slice(0, 30) + "..."}
          </div>
          <div className="text-xs text-slate-500 truncate">
            {row.original.author || "匿名"}
          </div>
        </div>
      );
    },
  },
  {
    accessorKey: "city_name",
    header: "城市",
    cell: ({ row }) => {
      const city = row.getValue("city_name") as string | null;
      return city ? <Badge variant="outline">{city}</Badge> : "-";
    },
  },
  {
    accessorKey: "topic",
    header: "话题",
    cell: ({ row }) => {
      const topic = row.getValue("topic") as string | null;
      return topic ? (
        <Badge variant="secondary" className="max-w-[80px] truncate">
          {topic}
        </Badge>
      ) : (
        "-"
      );
    },
  },
  {
    accessorKey: "post_type",
    header: "类型",
    cell: ({ row }) => {
      const type = row.getValue("post_type") as string;
      return (
        <Badge
          variant="outline"
          className={
            type === "post"
              ? "bg-blue-50 text-blue-700"
              : "bg-gray-50 text-gray-700"
          }
        >
          {type === "post" ? "帖子" : "回复"}
        </Badge>
      );
    },
  },
  {
    accessorKey: "likes",
    header: "点赞",
    cell: ({ row }) => (
      <div className="flex items-center gap-1">
        <ThumbsUp className="h-3 w-3 text-slate-400" />
        {row.getValue("likes")}
      </div>
    ),
  },
  {
    accessorKey: "replies_count",
    header: "回复",
    cell: ({ row }) => (
      <div className="flex items-center gap-1">
        <MessageCircle className="h-3 w-3 text-slate-400" />
        {row.getValue("replies_count")}
      </div>
    ),
  },
  {
    accessorKey: "data_source_name",
    header: "来源",
    cell: ({ row }) => (
      <Badge variant="outline" className="bg-green-50">
        {row.getValue("data_source_name") || "-"}
      </Badge>
    ),
  },
  {
    accessorKey: "posted_at",
    header: "发布时间",
    cell: ({ row }) => {
      const date = row.getValue("posted_at") as string | null;
      return date ? new Date(date).toLocaleDateString("zh-CN") : "-";
    },
  },
];

export default function ForumDataPage() {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [cityId, setCityId] = useState<string>("all");
  const [dataSourceId, setDataSourceId] = useState<string>("all");
  const [search, setSearch] = useState("");
  const [selectedPost, setSelectedPost] = useState<ForumPost | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  const { data: cities } = useQuery({
    queryKey: ["cities"],
    queryFn: () => api.cities.list(),
  });

  const { data: sources } = useQuery({
    queryKey: ["sources", { type: "forum" }],
    queryFn: () => api.sources.list({ type: "forum" }),
  });

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["forum", page, pageSize, cityId, dataSourceId, search],
    queryFn: () =>
      api.forum.list({
        skip: page * pageSize,
        limit: pageSize,
        city_id: cityId && cityId !== "all" ? parseInt(cityId) : undefined,
        data_source_id: dataSourceId && dataSourceId !== "all" ? parseInt(dataSourceId) : undefined,
        search: search || undefined,
      }),
  });

  const { data: stats } = useQuery({
    queryKey: ["forum-stats", cityId],
    queryFn: () => api.forum.stats(cityId && cityId !== "all" ? parseInt(cityId) : undefined),
  });

  const handleViewDetail = async (post: ForumPostListItem) => {
    try {
      const detail = await api.forum.get(post.id);
      setSelectedPost(detail);
      setDetailOpen(true);
    } catch (e) {
      console.error(e);
    }
  };

  const columnsWithActions: ColumnDef<ForumPostListItem>[] = [
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
              <MessageSquare className="h-8 w-8" />
              论坛数据
            </h1>
            <p className="text-slate-500">浏览已采集的论坛帖子和评论</p>
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
                <CardTitle className="text-sm text-slate-500">总帖子数</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-slate-500">总点赞数</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-pink-600">
                  {stats.total_likes}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-slate-500">总回复数</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">
                  {stats.total_replies}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-slate-500">平均点赞</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats.avg_likes ? stats.avg_likes.toFixed(1) : "-"}
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
              <div className="w-40">
                <Label>来源</Label>
                <Select value={dataSourceId} onValueChange={setDataSourceId}>
                  <SelectTrigger>
                    <SelectValue placeholder="全部来源" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">全部来源</SelectItem>
                    {sources?.map((source) => (
                      <SelectItem key={source.id} value={String(source.id)}>
                        {source.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex-1 min-w-[200px]">
                <Label>搜索</Label>
                <Input
                  placeholder="搜索标题、内容..."
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
          <SheetContent className="w-[600px] sm:max-w-[600px] overflow-y-auto">
            {selectedPost && (
              <>
                <SheetHeader>
                  <SheetTitle>
                    {selectedPost.title || "无标题"}
                  </SheetTitle>
                  <SheetDescription className="flex items-center gap-4">
                    <span className="flex items-center gap-1">
                      <User className="h-4 w-4" />
                      {selectedPost.author || "匿名"}
                    </span>
                    {selectedPost.posted_at && (
                      <span>
                        {new Date(selectedPost.posted_at).toLocaleString("zh-CN")}
                      </span>
                    )}
                  </SheetDescription>
                </SheetHeader>
                <div className="mt-6 space-y-4">
                  <div className="flex flex-wrap gap-2">
                    {selectedPost.city_name && (
                      <Badge variant="outline">{selectedPost.city_name}</Badge>
                    )}
                    {selectedPost.topic && (
                      <Badge variant="secondary">{selectedPost.topic}</Badge>
                    )}
                    {selectedPost.data_source_name && (
                      <Badge variant="outline" className="bg-green-50">
                        {selectedPost.data_source_name}
                      </Badge>
                    )}
                  </div>

                  <div className="flex gap-4 text-sm text-slate-500">
                    <span className="flex items-center gap-1">
                      <ThumbsUp className="h-4 w-4" />
                      {selectedPost.likes} 点赞
                    </span>
                    <span className="flex items-center gap-1">
                      <MessageCircle className="h-4 w-4" />
                      {selectedPost.replies_count} 回复
                    </span>
                    {selectedPost.views > 0 && (
                      <span>{selectedPost.views} 浏览</span>
                    )}
                  </div>

                  <div className="border rounded-lg p-4 bg-slate-50">
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">
                      {selectedPost.content}
                    </p>
                  </div>

                  {selectedPost.tags && (
                    <div className="flex flex-wrap gap-1">
                      {selectedPost.tags.split(",").map((tag, i) => (
                        <Badge key={i} variant="secondary" className="text-xs">
                          #{tag.trim()}
                        </Badge>
                      ))}
                    </div>
                  )}

                  {selectedPost.search_keyword && (
                    <div className="text-sm text-slate-500">
                      搜索关键词: {selectedPost.search_keyword}
                    </div>
                  )}

                  {selectedPost.source_url && (
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={() =>
                        window.open(selectedPost.source_url!, "_blank")
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
