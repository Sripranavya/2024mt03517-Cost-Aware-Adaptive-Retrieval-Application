import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// Mock the API client (hoisted so the mock factory can reference the fns).
const mocks = vi.hoisted(() => ({
  getToken: vi.fn(),
  clearToken: vi.fn(),
  apiLogin: vi.fn(),
  me: vi.fn(),
}));

vi.mock("../api/client", () => ({
  getToken: mocks.getToken,
  clearToken: mocks.clearToken,
  login: mocks.apiLogin,
  me: mocks.me,
}));

import { AuthProvider, useAuth } from "./AuthContext";

function Consumer() {
  const { user, loading, login, logout } = useAuth();
  if (loading) return <div>loading</div>;
  return (
    <div>
      <span data-testid="user">{user ? user.username : "anon"}</span>
      <button onClick={() => login("researcher", "local-demo")}>login</button>
      <button onClick={() => logout()}>logout</button>
    </div>
  );
}

function renderApp() {
  return render(
    <AuthProvider>
      <Consumer />
    </AuthProvider>,
  );
}

describe("AuthContext", () => {
  beforeEach(() => {
    mocks.getToken.mockReset();
    mocks.clearToken.mockReset();
    mocks.apiLogin.mockReset();
    mocks.me.mockReset();
  });

  it("starts anonymous when there is no token", async () => {
    mocks.getToken.mockReturnValue(null);
    renderApp();
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("anon"));
  });

  it("restores the session when a token is present", async () => {
    mocks.getToken.mockReturnValue("jwt");
    mocks.me.mockResolvedValue({ username: "researcher", issuer: "agentic-rag-local" });
    renderApp();
    await waitFor(() =>
      expect(screen.getByTestId("user")).toHaveTextContent("researcher"),
    );
  });

  it("logs in through the api and sets the user", async () => {
    mocks.getToken.mockReturnValue(null);
    mocks.apiLogin.mockResolvedValue("jwt");
    mocks.me.mockResolvedValue({ username: "researcher", issuer: "x" });
    renderApp();
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("anon"));
    await userEvent.click(screen.getByText("login"));
    await waitFor(() =>
      expect(screen.getByTestId("user")).toHaveTextContent("researcher"),
    );
    expect(mocks.apiLogin).toHaveBeenCalledWith("researcher", "local-demo");
  });

  it("clears the user on logout", async () => {
    mocks.getToken.mockReturnValue("jwt");
    mocks.me.mockResolvedValue({ username: "researcher", issuer: "x" });
    renderApp();
    await waitFor(() =>
      expect(screen.getByTestId("user")).toHaveTextContent("researcher"),
    );
    await userEvent.click(screen.getByText("logout"));
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("anon"));
    expect(mocks.clearToken).toHaveBeenCalled();
  });
});
