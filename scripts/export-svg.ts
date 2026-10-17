import { mkdirSync, writeFileSync } from "node:fs";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { CowboyDuck } from "../src/CowboyDuck";
import { Duck, type DuckExpression } from "../src/Duck";

const entries: Array<[React.ReactElement, string]> = [
  [React.createElement(Duck, { expression: "main" satisfies DuckExpression }), "duck-main"],
  [React.createElement(Duck, { expression: "wink" satisfies DuckExpression }), "duck-wink"],
  [React.createElement(Duck, { expression: "happy" satisfies DuckExpression }), "duck-happy"],
  [React.createElement(Duck, { expression: "curious" satisfies DuckExpression }), "duck-curious"],
  [React.createElement(CowboyDuck, { pose: "main" }), "cowboy-main"],
  [React.createElement(CowboyDuck, { pose: "wave" }), "cowboy-wave"],
];

mkdirSync("out/svg", { recursive: true });
for (const [element, name] of entries) {
  const html = renderToStaticMarkup(element);
  const start = html.indexOf("<svg");
  const end = html.indexOf("</svg>") + "</svg>".length;
  const svg = html
    .slice(start, end)
    .replace(
      'width="100%" height="100%"',
      'width="1080" height="1080" xmlns="http://www.w3.org/2000/svg"',
    );
  writeFileSync(`out/svg/${name}.svg`, `<?xml version="1.0" encoding="UTF-8"?>\n${svg}\n`, "utf8");
}
console.log(`exported ${entries.length} svg files`);
