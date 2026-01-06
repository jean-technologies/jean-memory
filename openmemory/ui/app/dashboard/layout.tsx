import { ScrollArea } from "@/components/ui/scroll-area";
import { DeprecationBanner } from "@/components/DeprecationBanner";

export default function DashboardNewLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <DeprecationBanner />
      <ScrollArea className="h-[calc(100vh-64px)]">
        {children}
      </ScrollArea>
    </>
  );
} 