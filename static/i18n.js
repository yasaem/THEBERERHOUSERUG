/* Translate interface text only. Escaped business data is protected with opaque
   placeholders until the translated markup has been serialized safely. */
const BazarI18n = (() => {
  let lang = "fr";
  try {
    lang = localStorage.getItem("bazar.language") === "en" ? "en" : "fr";
  } catch {}
  let catalogue = {},
    pattern;
  const literals = new Map();
  const prefix = "__BAZAR_" + crypto.randomUUID().replaceAll("-", "") + "_";
  let next = 0;
  const escape = (value) =>
    String(value ?? "").replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  const ready = fetch("/translations.json")
    .then((r) => {
      if (!r.ok) throw Error("Translation catalogue unavailable");
      return r.json();
    })
    .then((data) => {
      catalogue = data;
      pattern = new RegExp(
        "(?<![\\p{L}\\p{N}_])(" +
          Object.keys(data)
            .sort((a, b) => b.length - a.length)
            .map((s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
            .join("|") +
          ")(?![\\p{L}\\p{N}_])",
        "gu",
      );
    });
  function translate(text, selected = lang) {
    text = String(text ?? "");
    if (selected !== "en") return text;
    if (Object.hasOwn(catalogue, text)) return catalogue[text];
    text = text
      .replace(
        /(\d+) résultats?/g,
        (_, n) => n + (n === "1" ? " result" : " results"),
      )
      .replace(
        /(\d+) éléments? affichés?/g,
        (_, n) => n + (n === "1" ? " item displayed" : " items displayed"),
      )
      .replace(/(\d+) unités/g, (_, n) => n + (n === "1" ? " unit" : " units"));
    return pattern ? text.replace(pattern, (match) => catalogue[match]) : text;
  }
  function protect(value) {
    const token = prefix + next++ + "__";
    literals.set(token, escape(value));
    return token;
  }
  function html(markup, selected = lang) {
    const fragment = document.createElement("template");
    fragment.innerHTML = markup;
    const walker = document.createTreeWalker(
      fragment.content,
      NodeFilter.SHOW_TEXT,
    );
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (!node.parentElement?.closest("[data-no-i18n]")) {
        // Keep canonical option values stable when the visible label changes.
        if (
          node.parentElement?.tagName === "OPTION" &&
          !node.parentElement.hasAttribute("value")
        )
          node.parentElement.setAttribute(
            "value",
            node.parentElement.textContent,
          );
        node.textContent = translate(node.textContent, selected);
      }
    }
    fragment.content.querySelectorAll("*").forEach((el) => {
      if (el.closest("[data-no-i18n]")) return;
      for (const attr of ["placeholder", "title", "aria-label", "alt"])
        if (el.hasAttribute(attr))
          el.setAttribute(attr, translate(el.getAttribute(attr), selected));
    });
    const used = new Set();
    const result = fragment.innerHTML.replace(
      new RegExp(prefix + "\\d+__", "g"),
      (token) => {
        used.add(token);
        return literals.get(token) ?? "";
      },
    );
    used.forEach((token) => literals.delete(token));
    return result;
  }
  function setLanguage(value) {
    if (!["fr", "en"].includes(value)) return;
    lang = value;
    try {
      localStorage.setItem("bazar.language", lang);
    } catch {}
    document.documentElement.lang = lang;
    document.title =
      lang === "en"
        ? "Bazar — Retail management"
        : "Bazar — Gestion de vos commerces";
  }
  setLanguage(lang);
  return {
    ready,
    translate,
    protect,
    html,
    setLanguage,
    get language() {
      return lang;
    },
  };
})();
