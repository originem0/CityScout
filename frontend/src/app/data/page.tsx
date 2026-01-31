"use client";

import { AppLayout } from "@/components/layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Briefcase, Home, MessageSquare } from "lucide-react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

const dataCategories = [
  {
    title: "招聘数据",
    description: "浏览已采集的招聘信息",
    href: "/data/jobs",
    icon: Briefcase,
    color: "text-blue-600",
    bgColor: "bg-blue-50",
    statsKey: "jobs" as const,
  },
  {
    title: "租房数据",
    description: "浏览已采集的租房信息",
    href: "/data/rent",
    icon: Home,
    color: "text-orange-600",
    bgColor: "bg-orange-50",
    statsKey: "rent" as const,
  },
  {
    title: "论坛帖子",
    description: "浏览已采集的论坛帖子和评论",
    href: "/data/forum",
    icon: MessageSquare,
    color: "text-green-600",
    bgColor: "bg-green-50",
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
        <div>
          <h1 className="text-3xl font-bold">数据浏览</h1>
          <p className="text-slate-500">查看已采集的各类数据</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {dataCategories.map((category) => (
            <Link key={category.href} href={category.href}>
              <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
                <CardHeader>
                  <div className={`w-12 h-12 rounded-lg ${category.bgColor} flex items-center justify-center mb-2`}>
                    <category.icon className={`h-6 w-6 ${category.color}`} />
                  </div>
                  <CardTitle>{category.title}</CardTitle>
                  <CardDescription>{category.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">
                    {stats[category.statsKey].toLocaleString()}
                  </div>
                  <div className="text-sm text-slate-500">条数据</div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </AppLayout>
  );
}
