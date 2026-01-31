"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { ReactNode } from "react";

const routeLabels: Record<string, string> = {
  dashboard: "仪表盘",
  cities: "城市管理",
  keywords: "关键词",
  sources: "数据源",
  tasks: "爬虫任务",
  data: "数据浏览",
  jobs: "招聘数据",
  rent: "房租数据",
  forum: "论坛帖子",
  "manual-import": "手动导入",
  guide: "搜索指南",
  analysis: "数据分析",
  export: "数据导出",
  settings: "系统设置",
  logs: "系统日志",
};

interface HeaderProps {
  mobileMenuButton?: ReactNode;
}

export function Header({ mobileMenuButton }: HeaderProps) {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  // Build breadcrumb items
  const breadcrumbs = segments.map((segment, index) => {
    const path = "/" + segments.slice(0, index + 1).join("/");
    const label = routeLabels[segment] || segment;
    const isLast = index === segments.length - 1;

    return { path, label, isLast };
  });

  return (
    <header className="flex h-14 items-center gap-4 border-b bg-card px-4 md:px-6">
      {mobileMenuButton}

      {/* Breadcrumb Navigation */}
      <nav className="flex items-center gap-1 text-sm">
        {breadcrumbs.map((item, index) => (
          <div key={item.path} className="flex items-center gap-1">
            {index > 0 && (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
            {item.isLast ? (
              <span className="font-medium text-foreground">{item.label}</span>
            ) : (
              <Link
                href={item.path}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                {item.label}
              </Link>
            )}
          </div>
        ))}
      </nav>
    </header>
  );
}
