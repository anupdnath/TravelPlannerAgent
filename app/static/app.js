// Calls the MCP tools and draws the Prefab JSON that they return as HTML.
"use strict";

const view = document.getElementById("view");
const statusLine = document.getElementById("status");
let state = {};
let nextId = 1;
let latestRun = 0;

async function callTool(name, args) {
  const response = await fetch("/mcp", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json, text/event-stream",
    },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: nextId++,
      method: "tools/call",
      params: { name, arguments: args },
    }),
  });
  if (!response.ok) throw new Error(`The server returned HTTP ${response.status}.`);
  const body = await response.json();
  if (body.error) throw new Error(body.error.message);
  if (body.result.isError) throw new Error(body.result.content[0].text);
  return body.result.structuredContent;
}

function element(tag, node, text) {
  const el = document.createElement(tag);
  if (node.id) el.id = node.id;
  if (node.cssClass) el.className = node.cssClass;
  // textContent, never innerHTML: listing text comes from an outside website.
  if (text !== undefined) el.textContent = text;
  return el;
}

function bindValue(input, name) {
  input.addEventListener("input", () => {
    state[name] = input.value;
  });
}

function drawInput(node, type) {
  const input = element("input", node);
  input.type = type;
  input.name = node.name;
  if (node.placeholder && type !== "date") input.placeholder = node.placeholder;
  input.setAttribute("aria-labelledby", `${node.name}-label`);
  bindValue(input, node.name);
  return input;
}

function drawRadioGroup(node) {
  const group = element("div", node);
  group.classList.add("radio-group");
  group.setAttribute("role", "radiogroup");
  if (node.ariaLabelledBy) group.setAttribute("aria-labelledby", node.ariaLabelledBy);
  for (const radio of node.children) {
    const label = document.createElement("label");
    const input = document.createElement("input");
    input.type = "radio";
    input.id = radio.id;
    input.name = node.name;
    input.value = radio.option;
    bindValue(input, node.name);
    label.append(input, radio.label);
    group.append(label);
  }
  return group;
}

function isHttps(href) {
  try {
    return new URL(href).protocol === "https:";
  } catch {
    return false;
  }
}

function drawLink(node) {
  if (!isHttps(node.href)) return element("p", node, node.content);
  const link = element("a", node, node.content);
  link.href = node.href;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  return link;
}

function fillArguments(args) {
  const filled = {};
  for (const [key, value] of Object.entries(args)) {
    filled[key] = String(value).replace(/\{\{\s*(\w+)\s*\}\}/g, (_, name) => state[name] ?? "");
  }
  return filled;
}

function drawButton(node) {
  const button = element("button", node, node.label);
  button.type = "button";
  button.addEventListener("click", () => {
    const action = node.onClick;
    if (action?.action !== "toolCall") {
      showError(`The page does not support the action ${action?.action}.`);
      return;
    }
    run(button, action.tool, fillArguments(action.arguments));
  });
  return button;
}

const drawers = {
  Div: (node) => withChildren(element("div", node), node),
  Column: (node) => {
    const el = withChildren(element("div", node), node);
    el.classList.add("column");
    return el;
  },
  H3: (node) => element("h3", node, node.content),
  Text: (node) => element("p", node, node.content),
  Label: (node) => {
    const el = element("div", node, node.text);
    el.classList.add("field-label");
    return el;
  },
  Input: (node) => drawInput(node, node.inputType === "number" ? "number" : "text"),
  DatePicker: (node) => drawInput(node, "date"),
  RadioGroup: drawRadioGroup,
  Button: drawButton,
  Link: drawLink,
};

function withChildren(el, node) {
  for (const child of node.children ?? []) el.append(draw(child));
  return el;
}

function draw(node) {
  const drawer = drawers[node.type];
  if (drawer) return drawer(node);
  const unknown = document.createElement("p");
  unknown.className = "error";
  unknown.textContent = `The page cannot draw the component ${node.type}.`;
  return unknown;
}

function render(tree) {
  state = { ...(tree.state ?? {}) };
  view.replaceChildren(draw(tree.view));
}

function showError(message) {
  const error = document.createElement("p");
  error.className = "error";
  error.textContent = message;
  view.prepend(error);
}

async function run(button, tool, args) {
  // Only the newest run may draw, so an older response cannot replace a newer view.
  const thisRun = ++latestRun;
  button.disabled = true;
  statusLine.textContent = "Working. A search can take a few seconds.";
  try {
    const tree = await callTool(tool, args);
    if (thisRun === latestRun) render(tree);
  } catch (error) {
    if (thisRun === latestRun) showError(error.message);
  } finally {
    button.disabled = false;
    if (thisRun === latestRun) statusLine.textContent = "";
  }
}

document.getElementById("query-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const query = document.getElementById("query").value;
  run(document.getElementById("send"), "plan_stay", { query });
});
