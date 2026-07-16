import { defineCollection, z } from "astro:content";

const products = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    summary: z.string(),
    summary_th: z.string().optional(),
    flavor: z.string(),
    strength: z.number().min(1).max(7),
    type: z.enum(["pouch", "portion", "other"]).default("pouch"),
    tags: z.array(z.string()).default([]),
    image: z.string(),
    gallery: z.array(z.string()).default([]),
    featured: z.boolean().default(false),
    available: z.boolean().default(true),
    order: z.number().default(0),
  }),
});

const blog = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    title_th: z.string().optional(),
    description: z.string(),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    category: z.string().default("guides"),
    draft: z.boolean().default(false),
    heroImage: z.string().optional(),
  }),
});

export const collections = { products, blog };
