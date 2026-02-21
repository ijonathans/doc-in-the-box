import type { ButtonHTMLAttributes } from "react";
import { ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type PrimaryActionButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  iconOnly?: boolean;
};

export function PrimaryActionButton({ className, iconOnly = false, children, ...props }: PrimaryActionButtonProps) {
  return (
    <Button
      {...props}
      className={cn(
        "rounded-full bg-primary text-primary-foreground shadow-sm hover:bg-[#E85C1F]",
        iconOnly ? "h-12 w-12 p-0" : "h-12 px-6",
        className
      )}
    >
      {iconOnly ? <ArrowRight className="h-4 w-4" /> : children}
    </Button>
  );
}
