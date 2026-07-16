// @ts-check
import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";
import node from "@astrojs/node";

/** Multi-tenant white-label storefront (CARD-38 Phase C). SSR so brand data is live. */
export default defineConfig({
  output: "server",
  adapter: node({ mode: "standalone" }),
  integrations: [tailwind()],
  server: { port: 4321, host: true },
});
