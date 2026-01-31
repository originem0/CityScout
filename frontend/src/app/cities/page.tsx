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
import { Switch } from "@/components/ui/switch";
import { PageHeader } from "@/components/common/page-header";
import { EmptyState } from "@/components/common/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Plus, Pencil, Trash2, RefreshCw, MapPin } from "lucide-react";
import { useCities, useDeleteCity, useToggleCity } from "@/hooks/use-cities";
import { CityFormDialog } from "@/components/features/cities/city-form-dialog";
import { DeleteConfirmDialog } from "@/components/common/delete-confirm-dialog";
import { cn } from "@/lib/utils";
import type { City } from "@/types";

const tierLabels: Record<string, string> = {
  tier1: "一线",
  new_tier1: "新一线",
  tier2: "二线",
  tier3: "三线",
};

const tierColors: Record<string, { dot: string; text: string }> = {
  tier1: { dot: "bg-destructive", text: "text-destructive" },
  new_tier1: { dot: "bg-chart-3", text: "text-chart-3" },
  tier2: { dot: "bg-primary", text: "text-primary" },
  tier3: { dot: "bg-muted-foreground", text: "text-muted-foreground" },
};

export default function CitiesPage() {
  const { data: cities, isLoading, refetch } = useCities();
  const deleteCity = useDeleteCity();
  const toggleCity = useToggleCity();

  const [formOpen, setFormOpen] = useState(false);
  const [editingCity, setEditingCity] = useState<City | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deletingCity, setDeletingCity] = useState<City | null>(null);

  const handleAdd = () => {
    setEditingCity(null);
    setFormOpen(true);
  };

  const handleEdit = (city: City) => {
    setEditingCity(city);
    setFormOpen(true);
  };

  const handleDeleteClick = (city: City) => {
    setDeletingCity(city);
    setDeleteOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (deletingCity) {
      await deleteCity.mutateAsync(deletingCity.id);
      setDeleteOpen(false);
      setDeletingCity(null);
    }
  };

  const handleToggle = async (city: City) => {
    await toggleCity.mutateAsync(city.id);
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <PageHeader
          icon={MapPin}
          title="城市管理"
          description="管理需要采集数据的目标城市"
          actions={
            <>
              <Button variant="outline" size="icon" onClick={() => refetch()}>
                <RefreshCw className="h-4 w-4" />
              </Button>
              <Button onClick={handleAdd}>
                <Plus className="mr-2 h-4 w-4" />
                添加城市
              </Button>
            </>
          }
        />

        <Card>
          <CardHeader>
            <CardTitle>
              城市列表
              {cities && cities.length > 0 && (
                <span className="ml-2 text-sm font-normal text-muted-foreground">
                  共 {cities.length} 个城市，
                  {cities.filter((c) => c.enabled).length} 个已启用
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-4 py-3">
                    <Skeleton className="h-4 w-8" />
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-4 w-16" />
                    <Skeleton className="h-4 w-12" />
                    <Skeleton className="h-6 w-10 ml-auto" />
                  </div>
                ))}
              </div>
            ) : cities && cities.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[50px]">ID</TableHead>
                    <TableHead>城市名称</TableHead>
                    <TableHead>省份</TableHead>
                    <TableHead>城市级别</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead className="text-right">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {cities.map((city) => {
                    const tierConfig = tierColors[city.tier] || tierColors.tier3;
                    return (
                      <TableRow key={city.id}>
                        <TableCell className="text-muted-foreground">
                          {city.id}
                        </TableCell>
                        <TableCell className="font-medium">{city.name}</TableCell>
                        <TableCell>{city.province}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div
                              className={cn(
                                "w-2 h-2 rounded-full",
                                tierConfig.dot
                              )}
                            />
                            <span className={tierConfig.text}>
                              {tierLabels[city.tier] || city.tier}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Switch
                            checked={city.enabled}
                            onCheckedChange={() => handleToggle(city)}
                            disabled={toggleCity.isPending}
                          />
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleEdit(city)}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDeleteClick(city)}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            ) : (
              <EmptyState
                icon={MapPin}
                title="暂无城市数据"
                description="添加需要采集数据的目标城市"
                action={{
                  label: "添加第一个城市",
                  onClick: handleAdd,
                  icon: Plus,
                }}
              />
            )}
          </CardContent>
        </Card>
      </div>

      <CityFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        city={editingCity}
      />

      <DeleteConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        onConfirm={handleDeleteConfirm}
        title="删除城市"
        description={`确定要删除城市"${deletingCity?.name}"吗？相关的采集数据不会被删除。`}
        isLoading={deleteCity.isPending}
      />
    </AppLayout>
  );
}
