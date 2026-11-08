import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}
interface State {
  error: Error | null;
}

// App-level error boundary: a render error shows a friendly recovery card
// instead of a blank white screen, and is logged for diagnostics.
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // eslint-disable-next-line no-console
    console.error("UI error boundary caught:", error, info.componentStack);
  }

  private reset = (): void => this.setState({ error: null });

  render(): ReactNode {
    if (!this.state.error) return this.props.children;
    return (
      <div className="grid min-h-screen place-items-center px-4">
        <div className="card max-w-md p-8 text-center">
          <div className="mb-3 text-4xl">⚠️</div>
          <h1 className="text-lg font-bold text-slate-900">Something went wrong</h1>
          <p className="mt-1 text-sm text-slate-500">
            The interface hit an unexpected error. Your session is safe.
          </p>
          <pre className="mt-3 max-h-32 overflow-auto rounded-lg bg-slate-50 p-2 text-left text-xs text-slate-500">
            {this.state.error.message}
          </pre>
          <div className="mt-4 flex justify-center gap-2">
            <button onClick={this.reset} className="btn-primary px-4 py-2">
              Try again
            </button>
            <button onClick={() => window.location.reload()} className="btn-ghost px-4 py-2">
              Reload
            </button>
          </div>
        </div>
      </div>
    );
  }
}
