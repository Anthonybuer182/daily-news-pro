import { ReactNode } from 'react';
import { FilterProvider } from './context/FilterContext';

interface PreviewLayoutProps {
  children: ReactNode;
}

export default function PreviewLayout({ children }: PreviewLayoutProps) {
  return (
    <FilterProvider>
      {children}
    </FilterProvider>
  );
}