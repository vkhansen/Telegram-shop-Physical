// @ts-check
import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";
import sitemap from "@astrojs/sitemap";
import netlify from "@astrojs/netlify";

const site = process.env.PUBLIC_SITE_URL || "https://snusthai.example.com";

// https://astro.build/config
// hybrid: pages prerender by default; src/pages/api/* stay on-demand for Resend.
export default defineConfig({
  site,
  integrations: [tailwind(), sitemap()],
  output: "hybrid",
  adapter: netlify(),
  vite: {
    ssr: {
      noExternal: ["photoswipe"],
    },
  },
});
