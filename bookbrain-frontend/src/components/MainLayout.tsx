import { Header } from '@/components/Header';

interface MainLayoutProps {
  children: React.ReactNode;
  /** Open state for upload dialog */
  uploadDialogOpen?: boolean;
  /** Handler for upload dialog open state change */
  onUploadDialogOpenChange?: (open: boolean) => void;
  /** Handler for search shortcut click */
  onSearchClick?: () => void;
}

export function MainLayout({
  children,
  uploadDialogOpen,
  onUploadDialogOpenChange,
  onSearchClick,
}: MainLayoutProps) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header
        uploadDialogOpen={uploadDialogOpen}
        onUploadDialogOpenChange={onUploadDialogOpenChange}
        onSearchClick={onSearchClick}
      />
      <main className="flex flex-col items-center px-4 py-8">
        {children}
      </main>
    </div>
  );
}
