import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg font-display text-[13px] font-medium transition-colors duration-150 disabled:pointer-events-none disabled:opacity-50 focus-ring",
  {
    variants: {
      variant: {
        primary:
          "bg-brand text-white border border-transparent shadow-l1 hover:bg-brand-hover",
        secondary:
          "bg-white text-ink border border-line shadow-l1 hover:bg-canvas",
        ghost: "text-muted hover:text-ink hover:bg-canvas border border-transparent",
        ai: "bg-lavender text-brand border border-transparent hover:bg-brand hover:text-white",
        danger: "bg-white text-danger border border-line hover:bg-red-50",
      },
      size: {
        default: "h-9 px-3",
        compact: "h-[30px] px-2.5 text-[12.5px]",
        icon: "h-7 w-7 rounded-md",
        lg: "h-10 px-4 text-[14px]",
      },
    },
    defaultVariants: { variant: "secondary", size: "default" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  ),
);
Button.displayName = "Button";

export { buttonVariants };
