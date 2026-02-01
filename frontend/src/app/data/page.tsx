"use client";

import { AppLayout } from "@/components/layout";
import { PageHeader } from "@/components/common/page-header";
import { Briefcase, Home, MessageSquare, ArrowRight, Database } from "lucide-react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

const dataCategories = [
  {
    title: "招聘数据",
    description: "浏览已采集的招聘信息",
    href: "/data/jobs",
    icon: Briefcase,
    accent: "bg-primary",
    statsKey: "jobs" as const,
  },
  {
    title: "租房数据",
    description: "浏览已采集的租房信息",
    href: "/data/rent",
    icon: Home,
    accent: "bg-chart-3",
    statsKey: "rent" as const,
  },
  {
    title: "论坛帖子",
    description: "浏览已采集的论坛帖子和评论",
    href: "/data/forum",
    icon: MessageSquare,
    accent: "bg-chart-2",
    statsKey: "forum" as const,
  },
];

export default function DataPage() {
  const { data: jobStats } = useQuery({
    queryKey: ["jobs-stats"],
    queryFn: () => api.jobs.stats(),
  });

  const { data: rentStats } = useQuery({
    queryKey: ["rent-stats"],
    queryFn: () => api.rent.stats(),
  });

  const { data: forumStats } = useQuery({
    queryKey: ["forum-stats"],
    queryFn: () => api.forum.stats(),
  });

  const stats = {
    jobs: jobStats?.total || 0,
    rent: rentStats?.total || 0,
    forum: forumStats?.total || 0,
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <PageHeader
          icon={Database}
          title="数据浏览"
          description="查看已采集的各类数据"
        />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {dataCategories.map((category) => (
            <Link key={category.href} href={category.href}>
              <div className="group bg-card rounded-lg border shadow-soft card-hover p-6 h-full">
                <div className={cn("w-fit p-2.5 rounded-lg mb-4", category.accent)}>
                  <category.icon className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold mb-1">{category.title}</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  {category.description}
                </p>
                <div className="flex items-end justify-between">
                  <div>
                    <p className="text-3xl font-bold tabular-nums">
                      {stats[category.statsKey].toLocaleString()}
                    </p>
                    <p className="text-xs text-muted-foreground font-medium">
                      条数据
                    </p>
                  </div>
                  <ArrowRight className="h-5 w-5 text-muted-foreground group-hover:text-foreground group-hover:translate-x-1 transition-all" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </AppLayout>
  );
}
