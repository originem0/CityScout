"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageHeader } from "@/components/common/page-header";
import { EmptyState } from "@/components/common/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Plus, Pencil, Trash2, RefreshCw, Tags } from "lucide-react";
import { useKeywords, useDeleteKeyword } from "@/hooks/use-keywords";
import { KeywordFormDialog } from "@/components/features/keywords/keyword-form-dialog";
import { DeleteConfirmDialog } from "@/components/common/delete-confirm-dialog";
import { cn } from "@/lib/utils";
import type { Keyword } from "@/types";

const categoryLabels: Record<string, string> = {
  job_search: "招聘搜索",
  job_exclude: "招聘排除",
  forum_topic: "论坛话题",
};

const categoryColors: Record<string, string> = {
  job_search: "bg-success",
  job_exclude: "bg-destructive",
  forum_topic: "bg-chart-4",
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
        <PageHeader
          icon={Tags}
          title="关键词管理"
          description="管理搜索关键词和排除关键词"
          actions={
            <>
              <Button variant="outline" size="icon" onClick={() => refetch()}>
                <RefreshCw className="h-4 w-4" />
              </Button>
              <Button onClick={handleAdd}>
                <Plus className="mr-2 h-4 w-4" />
                添加关键词
              </Button>
            </>
          }
        />

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

        <div className="bg-card rounded-lg border shadow-soft">
          <div className="flex items-center justify-between p-6 border-b border-border">
            <h2 className="text-lg font-semibold">关键词列表</h2>
            {keywords && keywords.length > 0 && (
              <span className="text-sm text-muted-foreground">
                共 <span className="font-bold tabular-nums">{keywords.length}</span> 个关键词
              </span>
            )}
          </div>
          <div className="p-6">
            {isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-4 py-3">
                    <Skeleton className="h-4 w-8" />
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-6 w-20" />
                    <Skeleton className="h-6 w-16" />
                    <Skeleton className="h-8 w-16 ml-auto" />
                  </div>
                ))}
              </div>
            ) : keywords && keywords.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="w-[60px] text-xs font-medium text-muted-foreground">ID</TableHead>
                    <TableHead className="text-xs font-medium text-muted-foreground">关键词</TableHead>
                    <TableHead className="text-xs font-medium text-muted-foreground">类型</TableHead>
                    <TableHead className="text-xs font-medium text-muted-foreground">优先级</TableHead>
                    <TableHead className="text-xs font-medium text-muted-foreground">状态</TableHead>
                    <TableHead className="text-right text-xs font-medium text-muted-foreground">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {keywords.map((keyword) => (
                    <TableRow key={keyword.id} className="hover:bg-muted/50">
                      <TableCell className="text-muted-foreground tabular-nums">
                        {keyword.id}
                      </TableCell>
                      <TableCell className="font-medium">
                        {keyword.keyword}
                      </TableCell>
                      <TableCell>
                        <span
                          className={cn(
                            "inline-flex items-center px-2 py-0.5 text-xs font-medium text-white rounded-md",
                            categoryColors[keyword.category] || "bg-muted-foreground"
                          )}
                        >
                          {categoryLabels[keyword.category] || keyword.category}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span
                          className={cn(
                            "inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-md",
                            keyword.priority === "core"
                              ? "bg-primary text-primary-foreground"
                              : "bg-muted text-muted-foreground"
                          )}
                        >
                          {priorityLabels[keyword.priority] || keyword.priority}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span
                          className={cn(
                            "inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-md",
                            keyword.enabled
                              ? "bg-success text-white"
                              : "bg-muted text-muted-foreground"
                          )}
                        >
                          {keyword.enabled ? "启用" : "禁用"}
                        </span>
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
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <EmptyState
                icon={Tags}
                title="暂无关键词数据"
                description="点击添加关键词开始配置"
                action={{
                  label: "添加第一个关键词",
                  onClick: handleAdd,
                  icon: Plus,
                }}
              />
            )}
          </div>
        </div>
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
