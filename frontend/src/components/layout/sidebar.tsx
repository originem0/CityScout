"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  MapPin,
  Tags,
  Database,
  ListTodo,
  BarChart3,
  FileDown,
  Settings,
  Upload,
  Briefcase,
  Home,
  MessageSquare,
  ScrollText,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const navigation = [
  { name: "仪表盘", href: "/dashboard", icon: LayoutDashboard },
  { name: "城市管理", href: "/cities", icon: MapPin },
  { name: "关键词", href: "/keywords", icon: Tags },
  { name: "数据源", href: "/sources", icon: Database },
  { name: "爬虫任务", href: "/tasks", icon: ListTodo },
  {
    name: "数据浏览",
    href: "/data",
    icon: Briefcase,
    children: [
      { name: "招聘数据", href: "/data/jobs", icon: Briefcase },
      { name: "房租数据", href: "/data/rent", icon: Home },
      { name: "论坛帖子", href: "/data/forum", icon: MessageSquare },
    ],
  },
  { name: "手动导入", href: "/manual-import", icon: Upload },
  { name: "数据分析", href: "/analysis", icon: BarChart3 },
  { name: "数据导出", href: "/export", icon: FileDown },
  { name: "系统设置", href: "/settings", icon: Settings },
  { name: "系统日志", href: "/logs", icon: ScrollText },
];

interface SidebarContentProps {
  onNavigate?: () => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export function SidebarContent({
  onNavigate,
  collapsed = false,
  onToggleCollapse,
}: SidebarContentProps) {
  const pathname = usePathname();

  return (
    <div className="flex h-full flex-col bg-sidebar border-r border-sidebar-border">
      {/* Logo */}
      <div
        className={cn(
          "flex h-16 items-center border-b border-sidebar-border",
          collapsed ? "justify-center px-2" : "justify-between px-4"
        )}
      >
        <Link
          href="/dashboard"
          className="flex items-center gap-2"
          onClick={onNavigate}
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <MapPin className="h-5 w-5 text-primary-foreground" />
          </div>
          {!collapsed && (
            <span className="text-lg font-semibold text-foreground">
              CityScout
            </span>
          )}
        </Link>
        {onToggleCollapse && !collapsed && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleCollapse}
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-2 py-4">
        <div className="space-y-1">
          {navigation.map((item) => {
            const isActive =
              pathname === item.href || pathname.startsWith(item.href + "/");
            const Icon = item.icon;

            return (
              <div key={item.name}>
                <Link
                  href={item.href}
                  onClick={onNavigate}
                  className={cn(
                    "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    collapsed && "justify-center px-2",
                    isActive
                      ? "bg-sidebar-accent text-sidebar-primary"
                      : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                  )}
                  title={collapsed ? item.name : undefined}
                >
                  <Icon
                    className={cn(
                      "h-5 w-5 flex-shrink-0",
                      isActive
                        ? "text-sidebar-primary"
                        : "text-sidebar-foreground group-hover:text-sidebar-accent-foreground"
                    )}
                  />
                  {!collapsed && item.name}
                </Link>
                {/* Children - only show when not collapsed and parent is active */}
                {item.children && isActive && !collapsed && (
                  <div className="ml-4 mt-1 space-y-1 border-l-2 border-sidebar-border pl-4">
                    {item.children.map((child) => {
                      const ChildIcon = child.icon;
                      const isChildActive = pathname === child.href;
                      return (
                        <Link
                          key={child.href}
                          href={child.href}
                          onClick={onNavigate}
                          className={cn(
                            "flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors",
                            isChildActive
                              ? "text-sidebar-primary font-medium"
                              : "text-muted-foreground hover:text-sidebar-foreground"
                          )}
                        >
                          <ChildIcon className="h-4 w-4" />
                          {child.name}
                        </Link>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </nav>

      {/* Footer */}
      <div
        className={cn(
          "border-t border-sidebar-border p-4",
          collapsed && "px-2 py-3"
        )}
      >
        {collapsed ? (
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleCollapse}
            className="w-full h-8 text-muted-foreground hover:text-foreground"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        ) : (
          <p className="text-xs text-muted-foreground text-center">
            CityScout v1.0
          </p>
        )}
      </div>
    </div>
  );
}

interface SidebarProps {
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export function Sidebar({ collapsed = false, onToggleCollapse }: SidebarProps) {
  return (
    <div
      className={cn(
        "h-full transition-all duration-200",
        collapsed ? "w-16" : "w-52"
      )}
    >
      <SidebarContent collapsed={collapsed} onToggleCollapse={onToggleCollapse} />
    </div>
  );
}
