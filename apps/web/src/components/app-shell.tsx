import { FolderKanban, LayoutDashboard, LogOut, Upload, UserCircle2 } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { BrandMark } from "@/components/brand-mark";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { AuthUserButton, useAuthState } from "@/lib/auth";
import { cn } from "@/lib/utils";

const navigation = [
  { to: "/app", label: "Dashboard", icon: LayoutDashboard },
  { to: "/app/new", label: "New analysis", icon: Upload },
  { to: "/app/library", label: "Historical library", icon: FolderKanban },
];

export function AppShell() {
  const auth = useAuthState();
  const initials =
    auth.user?.firstName?.slice(0, 2).toUpperCase() ??
    auth.user?.email?.slice(0, 2).toUpperCase() ??
    "AN";

  return (
    <div className="min-h-screen bg-background">
      <header className="fixed inset-x-0 top-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-lg">
        <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-6 lg:px-10">
          <BrandMark />

          <nav className="hidden items-center gap-6 md:flex">
            {navigation.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/app"}
                className={({ isActive }) =>
                  cn(
                    "text-sm text-muted-foreground transition-colors hover:text-foreground",
                    isActive && "text-foreground",
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            {auth.clerkEnabled ? (
              <AuthUserButton />
            ) : (
              <>
                <Button asChild size="sm">
                  <NavLink to="/app/new">New analysis</NavLink>
                </Button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="icon-sm" className="rounded-full">
                      <Avatar size="sm">
                        <AvatarFallback>{initials}</AvatarFallback>
                      </Avatar>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="min-w-56">
                    <DropdownMenuLabel className="space-y-1">
                      <div className="text-sm font-medium text-foreground">{auth.user?.firstName ?? "Demo user"}</div>
                      <div className="text-xs text-muted-foreground">{auth.user?.email ?? "demo@and.local"}</div>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem asChild>
                      <NavLink to="/app">
                        <LayoutDashboard className="h-4 w-4" />
                        Dashboard
                      </NavLink>
                    </DropdownMenuItem>
                    <DropdownMenuItem asChild>
                      <NavLink to="/app/library">
                        <FolderKanban className="h-4 w-4" />
                        Previous analyses
                      </NavLink>
                    </DropdownMenuItem>
                    <DropdownMenuItem asChild>
                      <NavLink to="/app/new">
                        <Upload className="h-4 w-4" />
                        New analysis
                      </NavLink>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem>
                      <UserCircle2 className="h-4 w-4" />
                      Account
                    </DropdownMenuItem>
                    <DropdownMenuItem variant="destructive" onClick={auth.signOut}>
                      <LogOut className="h-4 w-4" />
                      Sign out
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl px-6 pt-28 pb-16 lg:px-10">
        <Outlet />
      </main>
    </div>
  );
}
