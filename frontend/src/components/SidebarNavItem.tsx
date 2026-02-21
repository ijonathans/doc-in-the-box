import type { LucideIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type SidebarNavItemProps = {
  icon: LucideIcon;
  label: string;
  active?: boolean;
  onClick?: () => void;
};

export function SidebarNavItem({ icon: Icon, label, active = false, onClick }: SidebarNavItemProps) {
  return (
    <Button
      type="button"
      variant="icon"
      size="sm"
      onClick={onClick}
      className={cn(
        "h-10 w-10 rounded-xl p-0 text-sidebar-foreground/80 hover:bg-white/10 hover:text-sidebar-foreground",
        active && "bg-primary text-white hover:bg-[#E85C1F] hover:text-white"
      )}
      aria-label={label}
      title={label}
    >
      <Icon className="h-4 w-4" />
    </Button>
  );
}
