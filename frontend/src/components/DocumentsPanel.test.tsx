import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DocumentsPanel } from "./DocumentsPanel";
import type { Document } from "../types/schemas";

function doc(overrides: Partial<Document> = {}): Document {
  return {
    id: "1",
    title: "France",
    source: "local_corpus",
    score: 0.9,
    text: "Paris is the capital of France.",
    ...overrides,
  };
}

describe("DocumentsPanel", () => {
  it("shows an empty state when there are no documents", () => {
    render(<DocumentsPanel documents={[]} />);
    expect(screen.getByText(/No documents were used/i)).toBeInTheDocument();
  });

  it("renders a row per document and expands the first by default", () => {
    render(<DocumentsPanel documents={[doc(), doc({ id: "2", title: "Japan" })]} />);
    expect(screen.getByText("France")).toBeInTheDocument();
    expect(screen.getByText("Japan")).toBeInTheDocument();
    expect(screen.getByText("Paris is the capital of France.")).toBeInTheDocument();
  });
});
