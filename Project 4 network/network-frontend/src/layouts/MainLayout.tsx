export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div>
      <nav className="bg-gray-100 p-4">
        <h1>Network</h1>
        {/* 之後這裡會放導航選項 */}
      </nav>
      <main className="container mx-auto p-4">{children}</main>
    </div>
  );
}
