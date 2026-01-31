"use client";

import { useState } from "react";
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
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Plus, Pencil, Trash2, RefreshCw } from "lucide-react";
import { useKeywords, useDeleteKeyword } from "@/hooks/use-keywords";
import { KeywordFormDialog } from "@/components/features/keywords/keyword-form-dialog";
import { DeleteConfirmDialog } from "@/components/common/delete-confirm-dialog";
import type { Keyword } from "@/types";

const categoryLabels: Record<string, string> = {
  job_search: "招聘搜索",
  job_exclude: "招聘排除",
  forum_topic: "论坛话题",
};

const categoryColors: Record<string, string> = {
  job_search: "bg-green-100 text-green-800",
  job_exclude: "bg-red-100 text-red-800",
  forum_topic: "bg-purple-100 text-purple-800",
};

const priorityLabels: Record<string, string> = {
  core: "核心",
  extended: "扩展",
};

export default function KeywordsPage() {
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const { data: keywords, isLoading, refetch } = useKeywords(
    categoryFilter !== "all" ? { category: categoryFilter } : undefined
  );
  const deleteKeyword = useDeleteKeyword();

  const [formOpen, setFormOpen] = useState(false);
  const [editingKeyword, setEditingKeyword] = useState<Keyword | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deletingKeyword, setDeletingKeyword] = useState<Keyword | null>(null);

  const handleAdd = () => {
    setEditingKeyword(null);
    setFormOpen(true);
  };

  const handleEdit = (keyword: Keyword) => {
    setEditingKeyword(keyword);
    setFormOpen(true);
  };

  const handleDeleteClick = (keyword: Keyword) => {
    setDeletingKeyword(keyword);
    setDeleteOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (deletingKeyword) {
      await deleteKeyword.mutateAsync(deletingKeyword.id);
      setDeleteOpen(false);
      setDeletingKeyword(null);
    }
  };

  // 统计各类关键词数量
  const allKeywords = keywords || [];
  const counts = {
    all: allKeywords.length,
    job_search: allKeywords.filter((k) => k.category === "job_search").length,
    job_exclude: allKeywords.filter((k) => k.category === "job_exclude").length,
    forum_topic: allKeywords.filter((k) => k.category === "forum_topic").length,
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">关键词管理</h1>
            <p className="text-slate-500">管理搜索关键词和排除关键词</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="icon" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Button onClick={handleAdd}>
              <Plus className="mr-2 h-4 w-4" />
              添加关键词
            </Button>
          </div>
        </div>

        <Tabs value={categoryFilter} onValueChange={setCategoryFilter}>
          <TabsList>
            <TabsTrigger value="all">全部 ({counts.all})</TabsTrigger>
            <TabsTrigger value="job_search">
              招聘搜索 ({counts.job_search})
            </TabsTrigger>
            <TabsTrigger value="job_exclude">
              招聘排除 ({counts.job_exclude})
            </TabsTrigger>
            <TabsTrigger value="forum_topic">
              论坛话题 ({counts.forum_topic})
            </TabsTrigger>
          </TabsList>
        </Tabs>

        <Card>
          <CardHeader>
            <CardTitle>
              关键词列表
              {keywords && keywords.length > 0 && (
                <span className="ml-2 text-sm font-normal text-slate-500">
                  共 {keywords.length} 个关键词
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <p className="text-center py-8 text-slate-500">加载中...</p>
            ) : keywords && keywords.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[50px]">ID</TableHead>
                    <TableHead>关键词</TableHead>
                    <TableHead>类型</TableHead>
                    <TableHead>优先级</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead className="text-right">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {keywords.map((keyword) => (
                    <TableRow key={keyword.id}>
                      <TableCell className="text-slate-500">
                        {keyword.id}
                      </TableCell>
                      <TableCell className="font-medium">
                        {keyword.keyword}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="secondary"
                          className={categoryColors[keyword.category] || ""}
                        >
                          {categoryLabels[keyword.category] || keyword.category}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            keyword.priority === "core" ? "default" : "outline"
                          }
                        >
                          {priorityLabels[keyword.priority] || keyword.priority}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={keyword.enabled ? "default" : "secondary"}
                        >
                          {keyword.enabled ? "启用" : "禁用"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleEdit(keyword)}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDeleteClick(keyword)}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="text-center py-12">
                <p className="text-slate-500 mb-4">
                  暂无关键词数据，点击"添加关键词"开始配置
                </p>
                <Button onClick={handleAdd}>
                  <Plus className="mr-2 h-4 w-4" />
                  添加第一个关键词
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <KeywordFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        keyword={editingKeyword}
      />

      <DeleteConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        onConfirm={handleDeleteConfirm}
        title="删除关键词"
        description={`确定要删除关键词"${deletingKeyword?.keyword}"吗？`}
        isLoading={deleteKeyword.isPending}
      />
    </AppLayout>
  );
}
