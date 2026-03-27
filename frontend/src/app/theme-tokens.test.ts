import { readFileSync } from "node:fs";
import path from "node:path";

describe("light theme tokens", () => {
  it("uses the light-blue + slate palette in root tokens", () => {
    const cssPath = path.resolve(__dirname, "./globals.css");
    const css = readFileSync(cssPath, "utf8");

    expect(css).toContain("--background: oklch(0.985 0.01 238);");
    expect(css).toContain("--primary: oklch(0.56 0.14 247);");
    expect(css).toContain("--secondary: oklch(0.95 0.02 236);");
    expect(css).toContain("--accent: oklch(0.93 0.03 220);");
  });
});
