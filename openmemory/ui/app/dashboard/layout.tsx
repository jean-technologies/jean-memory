import { ScrollArea } from "@/components/ui/scroll-area";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ScrollArea className="h-[calc(100vh-64px)]">
      {children}
    </ScrollArea>
  );
} 