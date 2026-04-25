import { Component, ErrorInfo, ReactNode } from "react";

type ErrorBoundaryProps = {
  children: ReactNode;
};

type ErrorBoundaryState = {
  hasError: boolean;
};

export default class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = {
    hasError: false
  };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("MMagent frontend render error", error, info);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <main className="app-shell">
          <section className="page-container">
            <section className="panel error-boundary-panel">
              <div className="panel-heading">
                <div>
                  <h2>Something interrupted the UI</h2>
                  <p className="panel-subtitle">
                    We kept the app safe, but the page needs a clean render.
                  </p>
                </div>
              </div>
              <p className="muted">
                This can happen if the browser or an extension rewrites page text
                while React is updating the interface.
              </p>
              <button
                type="button"
                className="primary-button"
                onClick={this.handleReload}
              >
                Reload App
              </button>
            </section>
          </section>
        </main>
      );
    }

    return this.props.children;
  }
}
