"use client";

import { useState } from "react";
import { Sidebar, SidebarContent } from "./sidebar";
import { Header } from "./header";
import {
  Sheet,
  SheetContent,
} from "@/components/ui/sheet";
import { Menu } from "lucide-react";

export function AppLayout({ children }: { children: React.ReactNode }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="flex h-screen bg-background">
      {/* Desktop Sidebar */}
      <div className="hidden lg:block">
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
      </div>

      {/* Mobile Sidebar */}
      <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
        <SheetContent side="left" className="w-56 p-0">
          <SidebarContent onNavigate={() => setMobileMenuOpen(false)} />
        </SheetContent>
      </Sheet>

      <div className="flex flex-1 flex-col overflow-hidden">
        <Header
          mobileMenuButton={
            <button
              className="flex lg:hidden h-9 w-9 items-center justify-center rounded-md border hover:bg-accent transition-colors"
              onClick={() => setMobileMenuOpen(true)}
            >
              <Menu className="h-5 w-5" />
            </button>
          }
        />
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="animate-fade-in max-w-[1400px]">{children}</div>
        </main>
      </div>
    </div>
  );
}
