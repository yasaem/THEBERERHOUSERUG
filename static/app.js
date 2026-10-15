let language = BazarI18n.language;
const tr = (text, selected = language) => BazarI18n.translate(text, selected);
const $ = (s) => document.querySelector(s),
  esc = (v) => BazarI18n.protect(v),
  fmt = (v) =>
    new Intl.NumberFormat(language === "en" ? "en-GB" : "fr-MA", {
      maximumFractionDigits: 2,
    }).format((v || 0) / 100),
  cash = (v) => fmt(v) + " MAD";
let state,
  page = "dashboard",
  shop = "",
  month = new Date().toISOString().slice(0, 7),
  query = "",
  register = false;
const nav = [
  ["dashboard", "◫", "Tableau de bord"],
  ["sales", "↗", "Ventes"],
  ["products", "▦", "Produits & stock"],
  ["clients", "♧", "Clients"],
  ["invoices", "▤", "Factures"],
  ["partners", "♧", "Guides & partenaires"],
  ["commissions", "◈", "Commissions"],
  ["expenses", "↙", "Dépenses"],
  ["employees", "♙", "Employés & salaires"],
  ["reports", "▥", "Rapports & statistiques"],
  ["shops", "⌂", "Boutiques"],
  ["settings", "⚙", "Paramètres"],
];
async function api(path, data) {
  const r = await fetch("/api/" + path, {
    method: data ? "POST" : "GET",
    headers: data
      ? {
          "Content-Type": "application/json",
          "X-App-Language": language,
          "X-CSRF-Token": state?.csrf || "",
        }
      : {},
    body: data ? JSON.stringify(data) : undefined,
  });
  const j = await r.json();
  if (!r.ok) throw Error(j.error);
  return j;
}
function toast(t, translate = true) {
  $("#toast").textContent = translate ? tr(t) : t;
  $("#toast").style.display = "block";
  setTimeout(() => ($("#toast").style.display = "none"), 4000);
}
async function load() {
  try {
    state = await api("state");
    render();
  } catch (e) {
    auth();
  }
}
function auth() {
  state = null;
  $("#app").innerHTML = BazarI18n.html(
    `<div class="auth"><section class="auth-story"><div class="brand"><span class="logo">b</span>bazar<small>GESTION DE COMMERCE</small></div><div><div class="nav-label" style="padding:0;color:#b7cbbf">PENSÉ POUR VOTRE COMMERCE</div><h1>Votre savoir-faire.<br>Notre sens<br>de la gestion.</h1><p>Des premières ventes aux grandes ambitions, gardez une vision claire de vos boutiques, de vos équipes et de vos résultats.</p></div><small style="color:#8ca99b">Fait pour les commerces d’ici. · Maroc</small></section><section class="auth-form"><div><h2>${register ? "Bienvenue chez Bazar" : "Heureux de vous retrouver"}</h2><p class="subtitle">${register ? "Créez votre espace et ouvrez votre première boutique." : "Connectez-vous à votre espace de gestion."}</p><form id="auth-form">${register ? '<label>Votre entreprise</label><input name="company" placeholder="La Maison Berbère" required><label>Votre nom</label><input name="name" placeholder="Prénom et nom" required>' : ""}<label>Adresse e-mail</label><input name="email" type="email" autocomplete="username" placeholder="vous@entreprise.ma" required><label>Mot de passe</label><input name="password" type="password" autocomplete="${register ? "new-password" : "current-password"}" minlength="10" placeholder="10 caractères minimum" required><div class="error" id="auth-error"></div><button class="primary">${register ? "Créer mon espace →" : "Se connecter →"}</button></form><div class="auth-switch">${register ? "Déjà un compte ?" : "Vous débutez sur Bazar ?"} <button id="switch-auth">${register ? "Se connecter" : "Créer mon espace"}</button></div><p class="note" style="text-align:center;margin-top:35px">Un espace privé pour votre entreprise.<br>Vos données sont enregistrées dans votre environnement.</p></div></section></div>`,
  );
  $("#switch-auth").onclick = () => {
    register = !register;
    auth();
  };
  mountLanguageSwitch();
  $("#auth-form").onsubmit = async (e) => {
    e.preventDefault();
    const b = e.target.querySelector("button");
    b.disabled = true;
    try {
      await api(
        register ? "register" : "login",
        Object.fromEntries(new FormData(e.target)),
      );
      await load();
    } catch (x) {
      $("#auth-error").textContent = x.message;
      b.disabled = false;
    }
  };
}
function rows(t, period = false) {
  return (state[t] || []).filter(
    (r) =>
      (!shop || !r.shop_id || String(r.shop_id) === shop) &&
      (!period || r.date?.startsWith(month)),
  );
}
function sales() {
  return rows("sales", true).filter((s) => s.status !== "Annulée");
}
function sum(a, k) {
  return a.reduce((v, r) => v + (r[k] || 0), 0);
}
function shopName(id) {
  return state.shops.find((s) => s.id === id)?.name || "—";
}
function badge(s) {
  return `<span class="badge ${s === "Annulée" ? "gray" : s === "Partielle" || s === "À payer" ? "amber" : ""}">● ${esc(tr(s))}</span>`;
}
function isOwner() {
  return ["owner", "manager"].includes(state.user.role);
}
function render() {
  const available = nav.filter(
    ([id]) =>
      (isOwner() &&
        !(
          state.user.role === "manager" &&
          ["settings", "shops", "clients", "partners"].includes(id)
        )) ||
      [
        "products",
        "sales",
        ...(state.user.role === "seller" ? ["commissions", "invoices"] : []),
      ].includes(id),
  );
  if (!available.some((x) => x[0] === page)) page = available[0][0];
  const title = nav.find((x) => x[0] === page)[2];
  $("#app").innerHTML = BazarI18n.html(
    `<aside><div class="brand"><span class="logo">b</span><div>bazar<small>GESTION DE COMMERCE</small></div></div><div class="workspace"><span>VOTRE ENTREPRISE</span>⌂ &nbsp; ${esc(state.company)}</div><div class="nav-label">ESPACE DE GESTION</div><nav>${available.map(([id, icon, label]) => `<button data-page="${id}" class="${page === id ? "active" : ""}"><i>${icon}</i>${label}</button>`).join("")}</nav><div class="sidebar-foot"><div class="avatar">${esc(state.user.name.slice(0, 2).toUpperCase())}</div><div style="flex:1;font-size:11px">${esc(state.user.name)}<small>${isOwner() ? "Administrateur" : state.user.role === "seller" ? "Vendeur" : "Opérateur"}</small></div><button class="quiet" id="logout" title="Déconnexion">⇥</button></div></aside><div class="shell"><header class="topbar"><div class="actions"><button class="mobile-menu quiet" id="menu">☰</button><div class="breadcrumb">Espace de gestion &nbsp; / &nbsp; <b>${title}</b></div></div><div class="top-right"><span><i class="online"></i> Espace connecté</span><div class="avatar">${esc(state.user.name.slice(0, 1))}</div></div></header><main><div class="heading"><div><h1>${page === "dashboard" ? "Vue d’ensemble" : title}</h1><p class="subtitle">${page === "dashboard" ? "Chaque détail compte. Gardez un œil sur l’essentiel." : descriptions[page] || "Retrouvez et gérez les données de votre entreprise."}</p></div><div class="actions">${isOwner() ? '<button id="export">↓ &nbsp; Exporter</button>' : ""}${["dashboard", "sales", "invoices"].includes(page) ? '<button class="primary" id="new-sale">＋ &nbsp; Nouvelle vente</button>' : isOwner() ? `<button class="primary" id="add">＋ &nbsp; ${addLabels[page] || "Ajouter"}</button>` : ""}</div></div><div class="filters"><select id="shop-filter"><option value="">Toutes les boutiques</option>${state.shops.map((s) => `<option value="${s.id}" ${String(s.id) === shop ? "selected" : ""}>${esc(s.name)}</option>`).join("")}</select><input type="month" id="month-filter" value="${month}"><span class="period">◷ &nbsp; Données actualisées à l’instant</span></div><div id="content"></div><footer class="page-foot"><span>© ${new Date().getFullYear()} Bazar. Votre commerce, en toute clarté.</span><span>Devise de gestion : MAD &nbsp; · &nbsp; Heure : UTC</span></footer></main></div>`,
  );
  document.querySelectorAll("[data-page]").forEach(
    (b) =>
      (b.onclick = () => {
        page = b.dataset.page;
        query = "";
        render();
      }),
  );
  $("#logout").onclick = async () => {
    await api("logout", {});
    auth();
  };
  $("#menu").onclick = () => $("aside").classList.toggle("open");
  $("#shop-filter").onchange = (e) => {
    shop = e.target.value;
    render();
  };
  $("#month-filter").onchange = (e) => {
    if (!e.target.value) {
      e.target.value = month;
      return;
    }
    month = e.target.value;
    render();
  };
  if ($("#new-sale")) $("#new-sale").onclick = newSale;
  if ($("#add"))
    $("#add").onclick = () =>
      createForm(
        page === "settings" ? "users" : page === "reports" ? "expenses" : page,
      );
  if ($("#export")) $("#export").onclick = exportData;
  if (page === "settings" && state.user.role === "owner") {
    const b = document.createElement("button");
    b.textContent = tr("Informations de facturation");
    b.onclick = companySettings;
    $(".heading .actions").prepend(b);
  }
  if (page === "products" && isOwner()) {
    const b = document.createElement("button");
    b.textContent = tr("↑ Importer");
    b.onclick = importStock;
    $(".heading .actions").prepend(b);
  }
  content();
  mountLanguageSwitch();
}
const descriptions = {
  sales: "Toutes vos ventes, du premier échange au dernier règlement.",
  products: "Votre catalogue et vos quantités, boutique par boutique.",
  commissions: "Une répartition transparente. Des règlements bien suivis.",
  employees: "Vos équipes, leurs salaires et les montants restant dus.",
  reports: "Comprenez vos revenus, vos charges et votre rentabilité.",
  settings: "Les accès et la traçabilité de votre entreprise.",
};
const addLabels = {
  products: "Ajouter un article",
  clients: "Ajouter un client",
  partners: "Ajouter un partenaire",
  expenses: "Ajouter une dépense",
  employees: "Ajouter un employé",
  shops: "Ajouter une boutique",
  settings: "Inviter un utilisateur",
  commissions: "Nouvelle vente",
  reports: "Ajouter une dépense",
};
function metrics() {
  const a = sales(),
    ids = new Set(a.map((x) => x.id)),
    com = rows("commissions").filter((c) => ids.has(c.sale_id)),
    expenses = rows("expenses", true),
    salary = rows("salaries", true);
  const revenue = sum(a, "total") - sum(a, "tax"),
    net =
      revenue -
      sum(a, "cost") -
      sum(a, "shipping") -
      sum(a, "bank") -
      sum(com, "amount") -
      sum(expenses, "amount") -
      sum(salary, "amount");
  return {
    a,
    com,
    revenue,
    net,
    paid: sum(a, "paid"),
    due: sum(a, "total") - sum(a, "paid"),
    expenses,
    salary,
  };
}
function dashboard(report = false) {
  const m = metrics();
  const cards = [
    [
      "Chiffre d’affaires HT",
      m.revenue,
      "↗",
      `${m.a.length} ventes sur la période`,
    ],
    ["Montant encaissé", m.paid, "▣", "Paiements clients reçus"],
    ["Reste à encaisser", m.due, "◷", "Créances clients de la période"],
    ["Résultat de gestion", m.net, "◈", "Après coûts, commissions et charges"],
  ];
  let out = `<div class="cards">${cards.map(([t, v, i, h], n) => `<div class="card ${n === 3 ? "highlight" : ""}"><div class="card-top">${t}<span class="metric-icon">${i}</span></div><div class="value">${fmt(v)} <small>MAD</small></div><div class="hint">${h}</div></div>`).join("")}</div>`;
  if (!state.sales?.length)
    out += `<div class="welcome"><div><b>Votre commerce prend place ici.</b><p>Ajoutez vos articles, puis enregistrez votre première vente pour voir vos résultats.</p></div><button id="onboard-stock">Ajouter des articles →</button></div>`;
  const history = Array.from({ length: 6 }, (_, i) => {
    const date = new Date(month + "-01T12:00:00Z");
    date.setUTCMonth(date.getUTCMonth() - 5 + i);
    const prefix = date.toISOString().slice(0, 7),
      s = rows("sales").filter(
        (s) => s.date.startsWith(prefix) && s.status !== "Annulée",
      );
    return {
      label: date.toLocaleDateString(language, {
        month: "short",
        timeZone: "UTC",
      }),
      v: sum(s, "total") - sum(s, "tax"),
      cost: sum(s, "cost") + sum(s, "shipping") + sum(s, "bank"),
    };
  });
  let max = Math.max(10000, ...history.map((x) => x.v));
  out += `<div class="grid"><section class="panel"><div class="panel-head"><div><h2>Évolution de l’activité</h2><p class="subtitle" style="margin-top:7px">Votre chiffre d’affaires sur les 6 derniers mois</p></div><div class="legend"><span><i class="dot"></i>Ventes HT</span><span><i class="dot light"></i>Coûts directs</span></div></div><div class="chart"><div class="axis">${[1, 0.75, 0.5, 0.25, 0].map((x) => `<span>${fmt(max * x)}</span>`).join("")}</div><div class="plot">${history.map((x) => `<div class="barpair" title="${x.label} : ${cash(x.v)}"><div class="bar" style="height:${(x.v / max) * 95}%"></div><div class="bar light" style="height:${(x.cost / max) * 95}%"></div><label>${x.label}</label></div>`).join("")}</div></div></section><section class="panel"><div class="panel-head"><h2>Répartition des charges</h2><span class="subtitle">Ce mois</span></div>${chargeChart(m)}</section></div>`;
  if (report)
    out += table(
      ["Indicateur", "Montant"],
      [
        ["Coût des marchandises", cash(sum(m.a, "cost"))],
        ["Commissions acquises", cash(sum(m.com, "amount"))],
        ["Shipping", cash(sum(m.a, "shipping"))],
        ["Frais bancaires", cash(sum(m.a, "bank"))],
        ["Dépenses engagées", cash(sum(m.expenses, "amount"))],
        ["Dépenses payées", cash(sum(m.expenses, "paid"))],
        ["Salaires dus", cash(sum(m.salary, "amount"))],
        ["Salaires payés", cash(sum(m.salary, "paid"))],
        [
          "Valeur du stock",
          cash(rows("products").reduce((n, p) => n + p.cost * p.quantity, 0)),
        ],
      ],
      "Détail financier",
    );
  else out += saleTable(m.a.slice(0, 5), "Dernières ventes");
  return out;
}
function chargeChart(m) {
  const values = [
      ["Marchandises", sum(m.a, "cost"), "#176b52"],
      ["Commissions", sum(m.com, "amount"), "#7ea888"],
      ["Salaires", sum(m.salary, "amount"), "#d4dfbd"],
      [
        "Autres charges",
        sum(m.expenses, "amount") + sum(m.a, "shipping") + sum(m.a, "bank"),
        "#e6b87b",
      ],
    ],
    total = values.reduce((v, x) => v + x[1], 0);
  let pos = 0;
  const gradient = values
    .map((x) => {
      let start = pos;
      pos += total ? (x[1] / total) * 100 : 0;
      return `${x[2]} ${start}% ${pos}%`;
    })
    .join(",");
  return `<div class="donut-wrap"><div class="donut" style="background:${total ? "conic-gradient(" + gradient + ")" : "#edf1e8"}"><div class="donut-center">${fmt(total)}<small>Total des charges · MAD</small></div></div></div>${values.map((x) => `<div class="category"><span><i class="dot" style="background:${x[2]}"></i>${x[0]}</span><b>${cash(x[1])}</b></div>`).join("")}`;
}
function table(head, body, title = "") {
  return `<section class="panel table-panel">${title ? `<div class="table-title"><h2>${title}</h2><span class="subtitle">${body.length} résultat${body.length > 1 ? "s" : ""}</span></div>` : ""}<div class="table-wrap"><table><thead><tr>${head.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${body.map((r) => `<tr>${r.map((v) => `<td>${v}</td>`).join("")}</tr>`).join("")}</tbody></table></div>${!body.length ? '<div class="empty">Aucun élément pour le moment. Ajoutez votre première donnée.</div>' : ""}<div class="table-footer">${body.length} élément${body.length > 1 ? "s" : ""} affiché${body.length > 1 ? "s" : ""}</div></section>`;
}
function saleTable(a, title = "Liste des ventes") {
  return table(
    [
      "N° vente",
      "Client",
      "Boutique",
      "Date",
      "Montant TTC",
      "Statut",
      "Actions",
    ],
    a.map((s) => [
      `<span style="color:var(--green)">VT-${String(s.id).padStart(5, "0")}</span>`,
      esc(s.client),
      esc(shopName(s.shop_id)),
      s.date.slice(0, 10),
      `<b>${cash(s.total)}</b>`,
      badge(s.status),
      `<button data-invoice="${s.id}" title="Facture">▤</button> ${isOwner() && s.status !== "Annulée" ? `<button data-pay="sales:${s.id}" title="Encaisser">＋</button> <button data-cancel="${s.id}" title="Annuler">×</button>` : ""}`,
    ]),
    title,
  );
}
function content() {
  let html = "";
  const filter = (a) =>
    a.filter(
      (r) =>
        !query ||
        Object.values(r).some((v) =>
          String(v).toLowerCase().includes(query.toLowerCase()),
        ),
    );
  switch (page) {
    case "dashboard":
      html = dashboard();
      break;
    case "reports":
      html = dashboard(true);
      break;
    case "sales":
    case "invoices":
      html = saleTable(
        filter(rows("sales", true)),
        page === "invoices" ? "Factures et règlements" : "Toutes les ventes",
      );
      break;
    case "products":
      html = table(
        [
          "Article",
          "Référence",
          "Catégorie",
          "Boutique",
          "Prix de vente",
          "Stock",
          "Actions",
        ],
        filter(rows("products")).map((p) => [
          esc(p.name),
          esc(p.reference),
          esc(p.category),
          esc(shopName(p.shop_id)),
          cash(p.price),
          `<span class="badge ${p.quantity < 5 ? "amber" : ""}">${p.active ? p.quantity + " unités" : "Archivé"}</span>`,
          isOwner()
            ? `<button data-edit="products:${p.id}" title="Modifier">✎</button> <button data-adjust="${p.id}">Ajuster</button> <button data-archive="${p.id}" title="Archiver / réactiver">${p.active ? "◫" : "↶"}</button>`
            : "",
        ]),
        "Catalogue des articles",
      );
      break;
    case "clients":
      html = table(
        ["Client", "E-mail", "Téléphone", "Adresse", "Actions"],
        filter(rows("clients")).map((c) => [
          esc(c.name),
          esc(c.email),
          esc(c.phone),
          esc(c.address),
          `<button data-edit="clients:${c.id}">Modifier</button>`,
        ]),
        "Fichier clients",
      );
      break;
    case "partners":
      html = table(
        ["Partenaire", "Type", "Actions"],
        filter(rows("partners")).map((p) => [
          esc(p.name),
          badge(p.kind),
          `<button data-edit="partners:${p.id}">Modifier</button>`,
        ]),
        "Vos intervenants",
      );
      break;
    case "commissions":
      html = table(
        [
          "Bénéficiaire",
          "Type",
          "Vente",
          "Base HT − shipping",
          "Commission",
          "Payé",
          "Restant",
          "Actions",
        ],
        filter(rows("commissions")).map((c) => [
          esc(c.partner),
          esc(tr(c.kind)),
          "VT-" + c.sale_id,
          cash(c.base),
          cash(c.amount),
          cash(c.paid),
          cash(c.amount - c.paid),
          isOwner() && c.paid < c.amount
            ? `<button data-pay="commissions:${c.id}">Régler</button>`
            : "—",
        ]),
        "Commissions acquises",
      );
      break;
    case "expenses":
      html = table(
        [
          "Dépense",
          "Catégorie",
          "Boutique",
          "Date",
          "Montant",
          "Payé",
          "Actions",
        ],
        filter(rows("expenses", true)).map((e) => [
          esc(e.name),
          esc(e.category),
          esc(shopName(e.shop_id)),
          esc(e.date),
          cash(e.amount),
          cash(e.paid),
          e.paid < e.amount
            ? `<button data-pay="expenses:${e.id}">Régler</button>`
            : "—",
        ]),
        "Charges de la période",
      );
      break;
    case "employees":
      html =
        table(
          ["Employé", "Poste", "Boutique", "Salaire de référence", "Actions"],
          filter(rows("employees")).map((e) => [
            esc(e.name),
            esc(e.position),
            esc(shopName(e.shop_id)),
            cash(e.salary),
            `<button data-edit="employees:${e.id}">Modifier</button> <button data-salary="${e.id}">Déclarer un salaire</button>`,
          ]),
          "Votre équipe",
        ) +
        '<div style="height:24px"></div>' +
        table(
          ["Employé", "Période", "Montant dû", "Payé", "Actions"],
          rows("salaries", true).map((s) => [
            esc(s.name),
            esc(s.date),
            cash(s.amount),
            cash(s.paid),
            s.paid < s.amount
              ? `<button data-pay="salaries:${s.id}">Régler</button>`
              : "—",
          ]),
          "Suivi des salaires",
        );
      break;
    case "shops":
      html = table(
        ["Boutique", "Adresse", "Articles", "Ventes", "Actions"],
        rows("shops").map((s) => [
          esc(s.name),
          esc(s.address),
          state.products.filter((p) => p.shop_id === s.id).length,
          state.sales.filter(
            (p) => p.shop_id === s.id && p.status !== "Annulée",
          ).length,
          `<button data-edit="shops:${s.id}">Modifier</button>`,
        ]),
        "Vos points de vente",
      );
      break;
    case "settings":
      html =
        table(
          ["Nom", "E-mail", "Rôle", "Statut", "Actions"],
          state.users.map((u) => [
            esc(u.name),
            esc(u.email),
            esc(
              tr(
                {
                  owner: "Administrateur",
                  manager: "Responsable de boutique",
                  seller: "Vendeur",
                  operator: "Opérateur",
                }[u.role] || u.role,
              ),
            ),
            badge(u.active ? "Actif" : "Désactivé"),
            `<button data-edit="users:${u.id}">Gérer l’accès</button>`,
          ]),
          "Utilisateurs",
        ) +
        '<div style="height:24px"></div>' +
        table(
          ["Opération", "Date"],
          state.audit.slice(0, 50).map((a) => [esc(tr(a.event)), esc(a.date)]),
          "Journal d’audit",
        );
      break;
  }
  $("#content").innerHTML = BazarI18n.html(
    (!["dashboard", "reports"].includes(page)
      ? `<input id="search" class="search" placeholder="Rechercher…" value="${esc(query)}">`
      : "") + html,
  );
  bindContent();
}
function bindContent() {
  document
    .querySelectorAll("[data-edit]")
    .forEach((b) => (b.onclick = () => editRecord(b.dataset.edit)));
  document.querySelectorAll("[data-archive]").forEach(
    (b) =>
      (b.onclick = async () => {
        const p = state.products.find((p) => p.id === +b.dataset.archive);
        try {
          await api("update", {
            entity: "products",
            id: p.id,
            values: { active: p.active ? 0 : 1 },
          });
          await load();
          toast(p.active ? "Article archivé" : "Article réactivé");
        } catch (e) {
          toast(e.message, false);
        }
      }),
  );
  if ($("#search"))
    $("#search").oninput = (e) => {
      const pos = e.target.selectionStart;
      query = e.target.value;
      content();
      $("#search").focus();
      $("#search").setSelectionRange(pos, pos);
    };
  document
    .querySelectorAll("[data-invoice]")
    .forEach((b) => (b.onclick = () => invoice(+b.dataset.invoice)));
  document
    .querySelectorAll("[data-pay]")
    .forEach((b) => (b.onclick = () => pay(b.dataset.pay)));
  document
    .querySelectorAll("[data-adjust]")
    .forEach((b) => (b.onclick = () => adjust(+b.dataset.adjust)));
  document.querySelectorAll("[data-salary]").forEach(
    (b) =>
      (b.onclick = () =>
        createForm(
          "salaries",
          state.employees.find((x) => x.id === +b.dataset.salary),
        )),
  );
  document
    .querySelectorAll("[data-cancel]")
    .forEach((b) => (b.onclick = () => cancelSale(+b.dataset.cancel)));
  if ($("#onboard-stock"))
    $("#onboard-stock").onclick = () => {
      page = "products";
      render();
      createForm("products");
    };
}
function modal(title, body, submit, label = "Enregistrer") {
  const m = $("#modal");
  m.innerHTML = BazarI18n.html(
    `<div class="modal-head"><h3>${title}</h3><button class="quiet" id="close-modal">✕</button></div><form id="modal-form">${body}<div class="error" id="modal-error"></div><div class="form-actions"><button type="button" id="cancel-modal">Annuler</button>${submit ? `<button class="primary" id="submit-modal">${label}</button>` : ""}</div></form>`,
  );
  $("#close-modal").onclick = $("#cancel-modal").onclick = () => m.close();
  $("#modal-form").onsubmit = async (e) => {
    e.preventDefault();
    $("#submit-modal").disabled = true;
    try {
      await submit(Object.fromEntries(new FormData(e.target)));
      m.close();
      await load();
      toast("Enregistrement effectué");
    } catch (x) {
      $("#modal-error").textContent = x.message;
      $("#submit-modal").disabled = false;
    }
  };
  if (!m.open) m.showModal();
}
function field(name, label, type = "text", value = "", options = []) {
  return `<div class="field"><label for="f-${name}">${label}</label>${type === "select" ? `<select id="f-${name}" name="${name}">${options.map(([v, l]) => `<option value="${esc(v)}" ${String(v) === String(value) ? "selected" : ""}>${esc(["role", "active", "kind"].includes(name) ? tr(l) : l)}</option>`).join("")}</select>` : `<input id="f-${name}" name="${name}" type="${type}" value="${esc(value)}" ${type === "number" ? 'min="0" step="0.01"' : ""} ${["name", "password"].includes(name) ? "required" : ""}>`}</div>`;
}
function createForm(t, employee) {
  if (t === "commissions") return newSale();
  const shops = state.shops.map((s) => [s.id, s.name]);
  let fields = [];
  if (["products", "expenses", "employees", "salaries"].includes(t))
    fields.push(
      field("shop_id", "Boutique", "select", employee?.shop_id || shop, shops),
    );
  if (t === "salaries")
    fields.push(
      field("employee_id", "Employé", "select", employee.id, [
        [employee.id, employee.name],
      ]),
    );
  fields.push(
    field(
      "name",
      t === "salaries" ? "Libellé / employé" : "Nom",
      "text",
      employee?.name || "",
    ),
  );
  switch (t) {
    case "shops":
      fields.push(field("address", "Adresse"));
      break;
    case "products":
      fields.push(
        field("reference", "Référence"),
        field("category", "Catégorie personnalisée"),
        field("cost", "Prix d’achat (MAD)", "number"),
        field("price", "Prix de vente (MAD)", "number"),
        field("quantity", "Quantité initiale", "number", "0"),
      );
      break;
    case "clients":
      fields.push(
        field("email", "E-mail", "email"),
        field("phone", "Téléphone"),
        field("address", "Adresse"),
      );
      break;
    case "partners":
      fields.push(
        field(
          "kind",
          "Type",
          "select",
          "Guide",
          ["Guide", "Agence", "Chauffeur", "Autre"].map((x) => [x, x]),
        ),
      );
      break;
    case "expenses":
      fields.push(
        field("category", "Catégorie"),
        field("date", "Date", "date", new Date().toISOString().slice(0, 10)),
        field("amount", "Montant (MAD)", "number"),
      );
      break;
    case "employees":
      fields.push(
        field("position", "Poste"),
        field("salary", "Salaire de référence (MAD)", "number"),
      );
      break;
    case "salaries":
      fields.push(
        field("date", "Période", "date", month + "-01"),
        field("amount", "Salaire dû (MAD)", "number", employee.salary / 100),
      );
      break;
    case "users":
      fields.push(
        field(
          "assigned_shop",
          "Boutique affectée (hors administrateur)",
          "select",
          shop,
          shops,
        ),
        field("email", "E-mail", "email"),
        field("password", "Mot de passe initial (10 caractères)", "password"),
        field("role", "Rôle", "select", "seller", [
          ["seller", "Vendeur"],
          ["operator", "Comptable / opérateur"],
          ["manager", "Responsable de boutique"],
          ["owner", "Administrateur"],
        ]),
      );
      break;
  }
  modal(
    "Ajouter · " +
      {
        products: "Article",
        shops: "Boutique",
        clients: "Client",
        partners: "Partenaire",
        expenses: "Dépense",
        employees: "Employé",
        salaries: "Salaire",
        users: "Utilisateur",
      }[t],
    `<div class="form-grid">${fields.join("")}</div>`,
    (values) => api("create", { entity: t, values }),
  );
}
function pay(spec) {
  const [entity, id] = spec.split(":"),
    r = state[entity].find((x) => x.id === +id),
    due = (entity === "sales" ? r.total : r.amount) - r.paid;
  modal(
    "Enregistrer un règlement",
    `<p class="note">Solde restant : ${cash(due)}. Ce règlement sera ajouté à l’historique.</p>${field("amount", "Montant du règlement (MAD)", "number", due / 100)}`,
    (d) => api("pay", { ...d, entity, id: +id }),
  );
}
function adjust(id) {
  const p = state.products.find((p) => p.id === id);
  modal(
    "Ajuster · " + esc(p.name),
    field("quantity", "Quantité réelle en stock", "number", p.quantity) +
      field("reason", "Motif de l’ajustement"),
    (d) => api("adjust", { ...d, id }),
  );
}
function cancelSale(id) {
  modal(
    "Annuler la vente VT-" + id,
    '<p>Le stock sera rétabli et les commissions non payées seront annulées.</p><p class="note">Les encaissements restent dans l’historique. Tout remboursement client doit être traité et rapproché séparément.</p>',
    () => api("cancel", { id }),
    "Confirmer l’annulation",
  );
}
let saleKey;
function newSale() {
  saleKey = crypto.randomUUID();
  modal(
    "Nouvelle vente",
    `<div class="form-grid">${field(
      "shop_id",
      "Boutique",
      "select",
      shop,
      state.shops.map((s) => [s.id, s.name]),
    )}${field("client", "Client (facultatif)")}</div><div class="section-label">ARTICLES DE LA VENTE</div><div class="sale-line sale-labels"><span>Article / désignation libre</span><span>Qté</span><span>Prix MAD</span><span>Coût libre MAD</span></div><div id="sale-lines"></div><button type="button" id="add-line">＋ Ajouter un article</button><div class="section-label">MONTANTS ET FRAIS · MAD</div><div class="form-grid">${field("discount", "Remise globale HT", "number", 0)}${field(
      "vat",
      "TVA",
      "select",
      0,
      [
        [0, "0 %"],
        [10, "10 %"],
        [20, "20 %"],
      ],
    )}${field("shipping", "Shipping supporté (déduit de l’assiette)", "number", 0)}${field("bank", "Frais bancaires", "number", 0)}${field("paid", "Montant encaissé", "number", 0)}</div><div class="section-label">COMMISSIONS ET INTERVENANTS</div><p class="note">Pour plusieurs vendeurs : même enveloppe (taux ou fixe), parts totalisant 100 %. Les guides et agences sont calculés indépendamment sur HT après remise − shipping.</p><div id="commission-lines"></div><button type="button" id="add-commission">＋ Ajouter un bénéficiaire</button><div id="sale-totals" class="totals"></div>`,
    async (d) => {
      d.key = saleKey;
      d.client = d.client || "Client de passage";
      d.lines = [...document.querySelectorAll(".item-line")].map((el) => ({
        product_id: +el.querySelector(".product").value || null,
        name: el.querySelector(".free-name").value,
        quantity: el.querySelector(".qty").value,
        price: el.querySelector(".price").value,
        cost: el.querySelector(".cost").value,
      }));
      d.commissions = [...document.querySelectorAll(".commission-line")].map(
        (el) => ({
          name: el.querySelector(".c-name").value,
          kind: el.querySelector(".c-kind").value,
          method: el.querySelector(".c-method").value,
          value: el.querySelector(".c-value").value,
          share: el.querySelector(".c-share").value,
          user_id: +el.querySelector(".c-user").value || null,
        }),
      );
      if (d.commissions.some((x) => !x.name.trim()))
        throw Error(tr("Nom du bénéficiaire requis"));
      const sellers = d.commissions.filter((x) => x.kind === "Vendeur");
      if (
        sellers.some(
          (x) => x.method !== sellers[0].method || x.value !== sellers[0].value,
        )
      )
        throw Error(
          tr("Les vendeurs doivent partager la même enveloppe de commission"),
        );
      await api("sales", d);
    },
    "Valider la vente",
  );
  $("#add-line").onclick = addLine;
  $("#add-commission").onclick = addCommission;
  $("#f-shop_id").onchange = () => {
    $("#sale-lines").innerHTML = BazarI18n.html("");
    addLine();
  };
  $("#modal-form").addEventListener("input", updateTotals);
  addLine();
}
function addLine() {
  const el = document.createElement("div");
  el.className = "sale-line item-line";
  el.innerHTML = BazarI18n.html(
    `<div><select class="product"><option value="">Article libre (hors stock)</option>${state.products
      .filter((p) => p.active && String(p.shop_id) === $("#f-shop_id").value)
      .map(
        (p) =>
          `<option value="${p.id}">${esc(p.name)} · ${p.quantity} en stock</option>`,
      )
      .join(
        "",
      )}</select><input class="free-name" placeholder="Désignation de l’article" required></div><input class="qty" type="number" min="1" step="1" value="1" required><input class="price" type="number" min="0" step="0.01" value="0" required><input class="cost" type="number" min="0" step="0.01" value="0"><button type="button" class="remove">×</button>`,
  );
  $("#sale-lines").append(el);
  el.querySelector(".product").onchange = (e) => {
    const p = state.products.find((p) => p.id === +e.target.value);
    el.querySelector(".free-name").hidden = !!p;
    el.querySelector(".free-name").required = !p;
    el.querySelector(".price").value = p ? p.price / 100 : 0;
    el.querySelector(".cost").disabled = !!p;
    el.querySelector(".cost").value = p ? (p.cost || 0) / 100 : 0;
    updateTotals();
  };
  el.querySelector(".remove").onclick = () => {
    el.remove();
    updateTotals();
  };
  updateTotals();
}
function addCommission() {
  const el = document.createElement("div");
  el.className = "commission-line";
  el.innerHTML = BazarI18n.html(
    `<div><input class="c-name" placeholder="Bénéficiaire" required><select class="c-user" title="Compte vendeur bénéficiaire"><option value="">Compte vendeur (facultatif)</option>${(state.users || []).map((u) => `<option value="${u.id}">${esc(u.name)}</option>`).join("")}</select></div><select class="c-kind">${["Guide", "Agence", "Chauffeur", "Vendeur", "Autre"].map((x) => `<option>${x}</option>`).join("")}</select><select class="c-method"><option value="percent">Taux %</option><option value="fixed">Fixe MAD</option></select><input class="c-value" type="number" min="0" step="0.01" placeholder="Taux / montant" value="0"><input class="c-share" type="number" min="0" max="100" value="100" title="Part du vendeur en %"><button type="button">×</button>`,
  );
  $("#commission-lines").append(el);
  el.querySelector("button").onclick = () => {
    el.remove();
    updateTotals();
  };
  updateTotals();
}
function updateTotals() {
  if (!$("#sale-totals")) return;
  let subtotal = 0,
    cost = 0;
  document.querySelectorAll(".item-line").forEach((e) => {
    const q = +e.querySelector(".qty").value;
    subtotal += q * Math.round(+e.querySelector(".price").value * 100);
    cost += q * Math.round(+e.querySelector(".cost").value * 100);
  });
  const val = (id) => Math.round((+$("#f-" + id).value || 0) * 100),
    ht = Math.max(0, subtotal - val("discount")),
    shipping = val("shipping"),
    base = Math.max(0, ht - shipping),
    tax = Math.round((ht * +$("#f-vat").value) / 100);
  let commission = 0;
  document.querySelectorAll(".commission-line").forEach((e) => {
    let c =
      e.querySelector(".c-method").value === "percent"
        ? Math.round((base * +e.querySelector(".c-value").value) / 100)
        : Math.round(+e.querySelector(".c-value").value * 100);
    if (e.querySelector(".c-kind").value === "Vendeur")
      c = Math.round((c * +e.querySelector(".c-share").value) / 100);
    commission += c;
  });
  $("#sale-totals").innerHTML = BazarI18n.html(
    [
      ["Total TTC", ht + tax],
      ["Assiette commissions", base],
      ["Commissions", commission],
      [
        "Contribution estimée HT ≈",
        ht - cost - shipping - val("bank") - commission,
      ],
    ]
      .map(([l, v]) => `<span>${l}<b>${cash(v)}</b></span>`)
      .join(""),
  );
}
async function invoice(id, invoiceLanguage = language) {
  const it = (text) => tr(text, invoiceLanguage);
  const invoiceCash = (value) =>
    new Intl.NumberFormat(invoiceLanguage === "en" ? "en-GB" : "fr-MA", {
      maximumFractionDigits: 2,
    }).format(value / 100) + " MAD";
  try {
    const {
      sale: s,
      lines,
      shop: sh,
      company: co,
    } = await api("invoice", { id });
    modal(
      "Facture · VT-" + id,
      `<div class="invoice-language"><label for="invoice-language">${tr("Langue de la facture")}</label> <select id="invoice-language"><option value="fr" ${invoiceLanguage === "fr" ? "selected" : ""}>Français</option><option value="en" ${invoiceLanguage === "en" ? "selected" : ""}>English</option></select></div><article class="invoice" data-no-i18n><header><div>${co.logo ? `<img src="${esc(co.logo)}" alt="Logo" style="max-width:100px;max-height:70px">` : ""}<h1>${esc(co.name)}</h1><p>${esc(sh.name)}<br>${esc(co.address || sh.address)}<br>ICE : ${esc(co.ice || "—")} · IF : ${esc(co.tax_id || "—")}</p></div><div><h2>${it("FACTURE")}</h2><p>F-${String(id).padStart(6, "0")}<br>${s.date.slice(0, 10)}</p></div></header><p>${it("Client :")} <b>${esc(s.client)}</b></p>${s.status === "Annulée" ? `<p>${it("VENTE ANNULÉE — document historique")}</p>` : ""}<table><thead><tr><th>${it("Désignation")}</th><th>${it("Quantité")}</th><th>${it("Prix HT")}</th><th>${it("Total HT")}</th></tr></thead><tbody>${lines.map((l) => `<tr><td>${esc(l.name)}</td><td>${l.quantity}</td><td>${invoiceCash(l.price)}</td><td>${invoiceCash(l.quantity * l.price)}</td></tr>`).join("")}</tbody></table><div class="invoice-total"><p class="note">${it("Sous-total HT :")} ${invoiceCash(s.subtotal)}<br>${it("Remise :")} ${invoiceCash(s.discount)}<br>${it("TVA :")} ${invoiceCash(s.tax)}</p><b>${it("Total TTC :")} ${invoiceCash(s.total)}</b><p class="note">${it("Payé :")} ${invoiceCash(s.paid)} · ${it("Restant")} : ${invoiceCash(s.total - s.paid)}</p></div><p class="note">${it("Document de gestion. Les mentions fiscales et la numérotation légale sont à valider avant émission commerciale.")}</p></article><button type="button" id="print-invoice" class="primary">Imprimer</button> <button type="button" id="download-invoice">↓ Télécharger le PDF</button> ${isOwner() ? '<button type="button" id="email-invoice">Envoyer par e-mail</button>' : ""}`,
      null,
    );
    $("#invoice-language").onchange = (e) => invoice(id, e.target.value);
    $("#download-invoice").onclick = () => downloadInvoice(id, invoiceLanguage);
    if ($("#email-invoice"))
      $("#email-invoice").onclick = () =>
        modal(
          "Envoyer la facture",
          field("email", "Destinataire", "email"),
          (d) =>
            api("invoice-email", {
              id,
              email: d.email,
              language: invoiceLanguage,
            }),
          "Envoyer",
        );
    $("#print-invoice").onclick = () => {
      document.body.classList.add("printing");
      window.print();
      document.body.classList.remove("printing");
    };
  } catch (e) {
    toast(e.message, false);
  }
}
function exportData() {
  const t =
    {
      dashboard: "sales",
      reports: "sales",
      invoices: "sales",
      settings: "audit",
    }[page] || page;
  const data = rows(t, ["sales", "expenses", "salaries"].includes(t));
  if (!data.length) return toast("Aucune donnée à exporter");
  const keys = Object.keys(data[0]).filter(
    (k) => !["company_id", "idempotency"].includes(k),
  );
  const cell = (v) =>
    '"' +
    String(v ?? "")
      .replace(/^[=+@-]/, "'$&")
      .replace(/"/g, '""') +
    '"';
  const text =
    "\ufeff" +
    [
      keys
        .map((k) =>
          cell(
            tr(
              {
                id: "Identifiant",
                shop_id: "Boutique (ID)",
                user_id: "Utilisateur (ID)",
                sale_id: "Vente (ID)",
                employee_id: "Employé (ID)",
                product_id: "Article (ID)",
                name: "Nom",
                reference: "Référence",
                category: "Catégorie",
                price: "Prix vente (centimes MAD)",
                cost: "Coût achat (centimes MAD)",
                quantity: "Quantité",
                active: "Actif",
                client: "Client",
                date: "Date",
                status: "Statut",
                subtotal: "Sous-total HT (centimes MAD)",
                discount: "Remise (centimes MAD)",
                tax: "TVA (centimes MAD)",
                total: "Total TTC (centimes MAD)",
                shipping: "Shipping (centimes MAD)",
                bank: "Frais bancaires (centimes MAD)",
                paid: "Payé (centimes MAD)",
                amount: "Montant (centimes MAD)",
                base: "Assiette commissions (centimes MAD)",
                salary: "Salaire (centimes MAD)",
                email: "E-mail",
                phone: "Téléphone",
                address: "Adresse",
                position: "Poste",
                role: "Rôle",
                kind: "Type",
                partner: "Bénéficiaire",
                method: "Méthode",
                value: "Valeur",
                reason: "Motif",
                event: "Opération",
              }[k] || k,
            ),
          ),
        )
        .join(";"),
      ...data.map((r) =>
        keys
          .map((k) =>
            cell(
              ["status", "role", "kind", "method"].includes(k)
                ? tr(r[k])
                : r[k],
            ),
          )
          .join(";"),
      ),
    ].join("\r\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(
    new Blob([text], { type: "text/csv;charset=utf-8" }),
  );
  a.download = `bazar-${t}-${month}-${language}.csv`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
BazarI18n.ready.then(load).catch(() => {
  $("#app").textContent =
    "Impossible de charger les traductions / Unable to load translations";
});

async function importStock() {
  modal(
    "Importer le stock",
    `<p class="note">Fichier CSV UTF-8 ou Excel .xlsx, première feuille, 1 000 articles maximum. Les doublons sont refusés et l’import est atomique.</p>${field(
      "shop_id",
      "Boutique",
      "select",
      shop,
      state.shops.map((s) => [s.id, s.name]),
    )}<div class="field" style="margin-top:16px"><label>Fichier</label><input type="file" id="import-file" accept=".csv,.xlsx" required></div><div id="import-preview"></div>`,
    async (d) => {
      if (!window.importRows)
        throw Error(tr("Sélectionnez et vérifiez un fichier"));
      const mapping = {};
      document
        .querySelectorAll("[data-map]")
        .forEach((e) => (mapping[e.dataset.map] = +e.value));
      if (mapping.name < 0 || mapping.reference < 0 || mapping.quantity < 0)
        throw Error(tr("Associez nom, référence et quantité"));
      const mapped = window.importRows.map((row) =>
        Object.fromEntries(
          Object.entries(mapping).map(([k, i]) => [
            k,
            i < 0
              ? ["cost", "price"].includes(k)
                ? 0
                : ""
              : row[i] || (["cost", "price", "quantity"].includes(k) ? 0 : ""),
          ]),
        ),
      );
      const result = await api("import", { shop_id: +d.shop_id, rows: mapped });
      toast(result.count + " articles importés");
      window.importRows = null;
    },
    "Valider l’import",
  );
  window.importRows = null;
  $("#import-file").onchange = async (e) => {
    try {
      window.importRows = null;
      const file = e.target.files[0];
      if (!file) return;
      if (file.size > 1300000)
        throw Error(tr("Fichier trop volumineux (1,3 Mo maximum)"));
      const content = await new Promise((resolve, reject) => {
        const r = new FileReader();
        r.onload = () => resolve(r.result.split(",")[1]);
        r.onerror = reject;
        r.readAsDataURL(file);
      });
      const p = await api("import-preview", { filename: file.name, content });
      window.importRows = p.rows;
      const cols = [
        ["name", "Nom"],
        ["reference", "Référence"],
        ["quantity", "Quantité"],
        ["category", "Catégorie"],
        ["cost", "Prix achat"],
        ["price", "Prix vente"],
      ];
      $("#import-preview").innerHTML = BazarI18n.html(
        `<div class="section-label">ASSOCIATION DES COLONNES</div><div class="form-grid">${cols.map(([k, l]) => `<div class="field"><label>${l}</label><select data-map="${k}"><option value="-1">Non associée</option>${p.headers.map((h, i) => `<option value="${i}" ${h.toLowerCase() === k || h.toLowerCase() === l.toLowerCase() ? "selected" : ""}>${esc(h)}</option>`).join("")}</select></div>`).join("")}</div><p class="note">${p.rows.length} lignes détectées. Aperçu des 5 premières lignes :</p>${table(
          p.headers.map(esc),
          p.rows.slice(0, 5).map((r) => r.map(esc)),
        )}`,
      );
    } catch (x) {
      $("#modal-error").textContent = x.message;
    }
  };
}

async function downloadInvoice(id, invoiceLanguage = language) {
  try {
    const r = await api("invoice-pdf", { id, language: invoiceLanguage });
    const a = document.createElement("a");
    const bytes = Uint8Array.from(atob(r.content), (x) => x.charCodeAt(0));
    a.href = URL.createObjectURL(
      new Blob([bytes], { type: "application/pdf" }),
    );
    a.download = r.filename;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  } catch (e) {
    toast(e.message, false);
  }
}
function companySettings() {
  const s = state.settings || {};
  let logo = s.logo || "";
  modal(
    "Informations de facturation",
    `<p class="note">Les nouvelles factures conservent ces informations au moment de la vente. Les anciennes factures restent inchangées.</p><div class="form-grid">${field("address", "Adresse légale", "text", s.address || "")}${field("ice", "ICE", "text", s.ice || "")}${field("tax_id", "Identifiant fiscal", "text", s.tax_id || "")}<div class="field"><label>Logo PNG / JPEG (500 Ko maximum)</label><input type="file" id="company-logo" accept="image/png,image/jpeg"></div></div>`,
    (d) => api("company-settings", { ...d, logo }),
  );
  $("#company-logo").onchange = async (e) => {
    const f = e.target.files[0];
    if (!f) return;
    if (f.size > 500000) {
      $("#modal-error").textContent = tr("Logo trop volumineux");
      return;
    }
    logo = await new Promise((resolve) => {
      const r = new FileReader();
      r.onload = () => resolve(r.result);
      r.readAsDataURL(f);
    });
  };
}

function editRecord(spec) {
  const [t, id] = spec.split(":"),
    r = state[t].find((r) => r.id === +id);
  const configs = {
    products: [
      ["name", "Nom"],
      ["reference", "Référence"],
      ["category", "Catégorie"],
      ["cost", "Prix achat MAD", "number"],
      ["price", "Prix vente MAD", "number"],
    ],
    clients: [
      ["name", "Nom"],
      ["email", "E-mail", "email"],
      ["phone", "Téléphone"],
      ["address", "Adresse"],
    ],
    partners: [
      ["name", "Nom"],
      ["kind", "Type"],
    ],
    employees: [
      ["name", "Nom"],
      ["position", "Poste"],
      ["salary", "Salaire de référence MAD", "number"],
    ],
    shops: [
      ["name", "Nom"],
      ["address", "Adresse"],
    ],
    users: [["name", "Nom"]],
  };
  let fields = configs[t].map(([k, l, type]) =>
    field(
      k,
      l,
      type || "text",
      ["cost", "price", "salary"].includes(k) ? r[k] / 100 : r[k],
    ),
  );
  if (t === "users")
    fields.push(
      field("role", "Rôle", "select", r.role, [
        ["owner", "Administrateur"],
        ["manager", "Responsable boutique"],
        ["seller", "Vendeur"],
        ["operator", "Opérateur"],
      ]),
      field("active", "État du compte", "select", r.active, [
        [1, "Actif"],
        [0, "Désactivé"],
      ]),
      field(
        "assigned_shop",
        "Boutique affectée (hors administrateur)",
        "select",
        shop,
        state.shops.map((s) => [s.id, s.name]),
      ),
      field("reset_password", "Nouveau mot de passe (facultatif)", "text", ""),
    );
  modal(
    t === "users" ? "Gérer l’accès" : "Modifier la fiche",
    `<div class="form-grid">${fields.join("")}</div>`,
    (values) => {
      if (t === "users") {
        values.active = +values.active;
        if (values.reset_password) values.password = values.reset_password;
        delete values.reset_password;
      }
      return api("update", { entity: t, id: +id, values });
    },
  );
  if (t === "users") $("#f-reset_password").type = "password";
}

function mountLanguageSwitch() {
  const wrapper = document.createElement("div");
  wrapper.className = "language-control";
  wrapper.innerHTML = `<label for="language-switch">${language === "en" ? "Language" : "Langue"}</label><select id="language-switch" aria-label="${language === "en" ? "Application language" : "Langue de l’application"}"><option value="fr" ${language === "fr" ? "selected" : ""}>Français</option><option value="en" ${language === "en" ? "selected" : ""}>English</option></select>`;
  const target = $(".top-right") || $(".auth-form");
  target.prepend(wrapper);
  wrapper.querySelector("select").onchange = (e) => {
    language = e.target.value;
    BazarI18n.setLanguage(language);
    if (state) render();
    else {
      const fields = Object.fromEntries(new FormData($("#auth-form")));
      auth();
      for (const [key, value] of Object.entries(fields))
        if ($("#auth-form").elements[key])
          $("#auth-form").elements[key].value = value;
    }
  };
}
