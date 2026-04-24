// .eleventy.js — configuration for Bathrooms by LV static site
//
// Content sources (Markdown files with YAML frontmatter) are in ./src/.
// Images and other static assets are copied from ./public/ and
// ./src/assets/ without transformation.

const pluginRss = require("@11ty/eleventy-plugin-rss");
const fs = require("fs");
const path = require("path");

module.exports = function (eleventyConfig) {
  // Passthrough: CSS, JS, images
  eleventyConfig.addPassthroughCopy({ "src/assets": "assets" });
  eleventyConfig.addPassthroughCopy({ "public": "/" });

  // RSS plugin (dateToRfc3339, htmlDateString etc. filters)
  eleventyConfig.addPlugin(pluginRss);

  // Collection: all project case studies, sorted newest first
  eleventyConfig.addCollection("projects", (api) => {
    return api
      .getFilteredByGlob("src/projects/*.md")
      .sort((a, b) => b.date - a.date);
  });

  // Filter: format a date as e.g. "November 2021"
  eleventyConfig.addFilter("monthYear", (d) => {
    if (!d) return "";
    const date = d instanceof Date ? d : new Date(d);
    return date.toLocaleDateString("en-GB", { month: "long", year: "numeric" });
  });

  // Filter: UK-style date like "22 November 2021"
  eleventyConfig.addFilter("ukDate", (d) => {
    if (!d) return "";
    const date = d instanceof Date ? d : new Date(d);
    return date.toLocaleDateString("en-GB", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  });

  // Shortcode: gallery thumbnails for a project folder
  // Usage in template: {% gallery "slug-folder-name" %}
  eleventyConfig.addShortcode("gallery", function (dir) {
    const fullDir = path.join(__dirname, "public", "images", "projects", dir);
    if (!fs.existsSync(fullDir)) return "";
    const files = fs
      .readdirSync(fullDir)
      .filter((f) => /\.(jpe?g|png|webp)$/i.test(f))
      .sort();
    if (!files.length) return "";
    const items = files
      .map(
        (f) =>
          `    <li><img src="/images/projects/${dir}/${f}" alt="" loading="lazy"></li>`,
      )
      .join("\n");
    return `<ul class="gallery">\n${items}\n  </ul>`;
  });

  return {
    dir: {
      input: "src",
      output: "_site",
      includes: "_includes",
      data: "_data",
    },
    markdownTemplateEngine: "njk",
    htmlTemplateEngine: "njk",
    templateFormats: ["md", "njk", "html"],
  };
};
