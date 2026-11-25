import type { ReactNode } from 'react';
import { ScrollView, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { OfflineBanner } from '@/components/OfflineBanner';
import { cn } from '@/utils/cn';

interface ScreenProps {
  children: ReactNode;
  /** Sticky area at the bottom (main action). */
  footer?: ReactNode;
  scroll?: boolean;
  className?: string;
}

/** Page shell: safe area, offline banner, scrollable content so large fonts never clip. */
export function Screen({ children, footer, scroll = true, className }: ScreenProps) {
  const body = scroll ? (
    <ScrollView
      contentContainerClassName={cn('grow gap-lg px-lg py-xl', className)}
      keyboardShouldPersistTaps="handled"
    >
      {children}
    </ScrollView>
  ) : (
    <View className={cn('flex-1 gap-lg px-lg py-xl', className)}>{children}</View>
  );
  return (
    <SafeAreaView className="flex-1 bg-background" edges={['top', 'bottom', 'left', 'right']}>
      <OfflineBanner />
      {body}
      {footer ? <View className="gap-sm px-lg pb-lg pt-sm">{footer}</View> : null}
    </SafeAreaView>
  );
}
