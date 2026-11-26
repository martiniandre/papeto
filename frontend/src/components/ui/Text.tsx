import { Text as RNText, type TextProps as RNTextProps } from 'react-native';

import { cn } from '@/utils/cn';

type Variant = 'display' | 'title' | 'subtitle' | 'body' | 'secondary' | 'caption';

const variants: Record<Variant, string> = {
  display: 'font-heading text-display text-ink',
  title: 'font-heading text-title text-ink',
  subtitle: 'font-semibold text-subtitle text-ink',
  body: 'font-body text-body text-ink',
  secondary: 'font-body text-body text-ink-secondary',
  caption: 'font-semibold text-caption text-ink-secondary',
};

export interface TextProps extends RNTextProps {
  variant?: Variant;
  className?: string;
}

/** Base text. Never give it a fixed height: it must grow with large system fonts. */
export function Text({ variant = 'body', className, accessibilityRole, ...props }: TextProps) {
  return (
    <RNText
      accessibilityRole={
        accessibilityRole ?? (variant === 'title' || variant === 'display' ? 'header' : undefined)
      }
      className={cn(variants[variant], className)}
      {...props}
    />
  );
}
