import { render, screen } from "@testing-library/react";

vi.mock("next/font/google", () => ({
  Manrope: () => ({ variable: "--font-sans" }),
  Newsreader: () => ({ variable: "--font-heading" }),
}));

import Home from "@/app/page";
import { metadata } from "@/app/layout";

vi.mock("@/hooks/use-generation-stream", () => ({
  useGenerationStream: () => ({
    events: [],
    result: null,
    isLoading: false,
    error: null,
    generate: vi.fn(),
    reset: vi.fn(),
  }),
}));

describe("UI branding", () => {
  it("uses LinkedIn Comments Adviser in metadata title", () => {
    expect(metadata.title).toBe("LinkedIn Comments Adviser");
  });

  it("shows LinkedIn Comments Adviser on the landing page", () => {
    render(<Home />);

    expect(screen.getByText(/linkedin comments adviser/i)).toBeInTheDocument();
  });

  it("shows concise hero copy while preserving intent", () => {
    render(<Home />);

    expect(
      screen.getByRole("heading", {
        name: "Find public LinkedIn posts worth engaging with and get three ready replies per post.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Set your angle, watch progress, and review three ranked opportunities without dashboard noise.",
      ),
    ).toBeInTheDocument();
  });

  it("uses the updated cool light gradient in the hero surface", () => {
    render(<Home />);

    const main = screen.getByRole("main");
    expect(main.className).toContain(
      "bg-[radial-gradient(circle_at_top,_rgba(247,252,255,0.96),_rgba(230,242,255,0.88)_40%,_rgba(214,231,249,0.78)_100%)]",
    );
  });
});
