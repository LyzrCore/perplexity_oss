"use client";

import React, { useMemo } from "react";
import dynamic from "next/dynamic";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
// import { AuthProvider } from "@/contexts/AuthContext";

const NoSsrAuthProviderComponent = dynamic(
  () => import("@/contexts/AuthContext").then((mod) => mod.AuthProvider),
  {
    ssr: false,
  }
);

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = React.useState(() => new QueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <NoSsrAuthProviderComponent>{children}</NoSsrAuthProviderComponent>
    </QueryClientProvider>
  );
}
