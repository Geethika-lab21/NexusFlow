import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertOctagon } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught component error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[400px] flex-col items-center justify-center rounded-2xl border border-rose-200 bg-white p-8 text-center shadow-sm">
          <div className="mb-4 rounded-full bg-rose-50 p-3 text-rose-600">
            <AlertOctagon className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-[#17203d]">Something went wrong</h2>
          <p className="mt-2 max-w-md text-sm text-[#687391]">
            {this.state.error?.message || 'An unexpected rendering error occurred in the user interface.'}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-6 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white transition-colors hover:bg-indigo-500"
          >
            Reload Application
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
