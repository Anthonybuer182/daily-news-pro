import { ReactNode } from 'react';
import { ThemeProvider } from './context/ThemeContext';
import { FilterProvider } from './context/FilterContext';

interface PreviewLayoutProps {
  children: ReactNode;
}

export default function PreviewLayout({ children }: PreviewLayoutProps) {
  return (
    <ThemeProvider>
      <FilterProvider>
        {children}
      </FilterProvider>
    </ThemeProvider>
  );
}