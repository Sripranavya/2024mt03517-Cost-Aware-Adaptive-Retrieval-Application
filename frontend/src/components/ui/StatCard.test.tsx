import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatCard } from "./StatCard";

describe("StatCard", () => {
  it("renders the label, value and sub text", () => {
    render(<StatCard label="Hops" value={2} sub="lower is better" icon="🔁" />);
    expect(screen.getByText("Hops")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("lower is better")).toBeInTheDocument();
  });

  it("renders a string value without a sub line", () => {
    render(<StatCard label="Cost" value="$0.001" />);
    expect(screen.getByText("$0.001")).toBeInTheDocument();
  });
});
