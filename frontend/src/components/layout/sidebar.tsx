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
  Compass,
} from "lucide-react";

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
          collapsed ? "justify-center px-3" : "justify-between px-4"
        )}
      >
        <Link
          href="/dashboard"
          className="flex items-center gap-2.5 group"
          onClick={onNavigate}
        >
          <div className="flex h-9 w-9 items-center justify-center bg-primary rounded-lg">
            <Compass className="h-5 w-5 text-primary-foreground" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="text-base font-semibold tracking-tight text-sidebar-foreground">
                CityScout
              </span>
              <span className="text-[10px] text-muted-foreground">
                城市数据分析
              </span>
            </div>
          )}
        </Link>
        {onToggleCollapse && !collapsed && (
          <button
            onClick={onToggleCollapse}
            className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-sidebar-accent transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
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
                    "group flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors",
                    collapsed && "justify-center px-2",
                    isActive
                      ? "bg-sidebar-primary text-sidebar-primary-foreground"
                      : "text-sidebar-foreground hover:text-foreground hover:bg-sidebar-accent"
                  )}
                  title={collapsed ? item.name : undefined}
                >
                  <Icon
                    className={cn(
                      "h-[18px] w-[18px] flex-shrink-0",
                      isActive
                        ? "text-sidebar-primary-foreground"
                        : "text-muted-foreground group-hover:text-foreground"
                    )}
                  />
                  {!collapsed && <span>{item.name}</span>}
                </Link>
                {/* Children */}
                {item.children && isActive && !collapsed && (
                  <div className="ml-5 mt-1 space-y-0.5 border-l border-sidebar-border pl-3">
                    {item.children.map((child) => {
                      const ChildIcon = child.icon;
                      const isChildActive = pathname === child.href;
                      return (
                        <Link
                          key={child.href}
                          href={child.href}
                          onClick={onNavigate}
                          className={cn(
                            "flex items-center gap-2 px-2 py-1.5 text-sm rounded-md transition-colors",
                            isChildActive
                              ? "text-primary font-medium bg-sidebar-accent"
                              : "text-muted-foreground hover:text-foreground hover:bg-sidebar-accent"
                          )}
                        >
                          <ChildIcon className="h-3.5 w-3.5" />
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
          "border-t border-sidebar-border p-3",
          collapsed && "px-2"
        )}
      >
        {collapsed ? (
          <button
            onClick={onToggleCollapse}
            className="flex w-full h-8 items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-sidebar-accent transition-colors"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        ) : (
          <div className="flex items-center justify-between px-1">
            <span className="text-xs text-muted-foreground">
              v1.0.0
            </span>
            <div className="flex items-center gap-1.5">
              <div className="h-2 w-2 rounded-full bg-success" />
              <span className="text-xs text-muted-foreground">在线</span>
            </div>
          </div>
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
        collapsed ? "w-16" : "w-56"
      )}
    >
      <SidebarContent collapsed={collapsed} onToggleCollapse={onToggleCollapse} />
    </div>
  );
}
