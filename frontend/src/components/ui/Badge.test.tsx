import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Pill, StrategyBadge } from "./Badge";

describe("StrategyBadge", () => {
  it("shows the friendly label and a PROPOSED tag for the POMDP strategy", () => {
    render(<StrategyBadge name="pomdp" />);
    expect(screen.getByText("POMDP")).toBeInTheDocument();
    expect(screen.getByText("PROPOSED")).toBeInTheDocument();
  });

  it("falls back to the raw name for an unknown strategy", () => {
    render(<StrategyBadge name="mystery" useLabel={false} />);
    expect(screen.getByText("mystery")).toBeInTheDocument();
  });
});

describe("Pill", () => {
  it("renders its children", () => {
    render(<Pill>hello</Pill>);
    expect(screen.getByText("hello")).toBeInTheDocument();
  });
});
