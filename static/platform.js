/* Publisher-only UI. Every platform operation is authorised again by the API. */
function publisherRender() {
  const customers = state.companies,
    active = customers.filter((c) => c.subscription.accessible).length;
  $("#app").innerHTML = BazarI18n.html(
    `<div class="publisher"><header class="topbar"><div class="brand" style="padding:0"><span class="logo">b</span><div>bazar<small>ÉDITEUR SAAS</small></div></div><div class="top-right"><span>${esc(state.user.name)}</span><button id="publisher-password">Mon mot de passe</button><button id="logout">Déconnexion</button></div></header><main><div class="heading"><div><h1>Votre plateforme, vos clients.</h1><p class="subtitle">Créez les accès, suivez les abonnements et accompagnez chaque entreprise.</p></div><button class="primary" id="create-company">＋ Nouvelle entreprise</button></div><div class="cards"><div class="card"><div class="card-top">Entreprises clientes</div><div class="value">${customers.length}</div></div><div class="card"><div class="card-top">Accès ouverts</div><div class="value">${active}</div></div><div class="card"><div class="card-top">Accès suspendus ou expirés</div><div class="value">${customers.length - active}</div></div><div class="card highlight"><div class="card-top">Règlements enregistrés</div><div class="value">${cash(state.subscription_payments.reduce((v, p) => v + p.amount, 0))}</div><div class="hint">200 derniers règlements maximum</div></div></div>${table(
      [
        "Entreprise",
        "Administrateur client",
        "Formule",
        "Statut",
        "Échéance",
        "Utilisation",
        "Actions",
      ],
      customers.map((c) => {
        const a = c.subscription;
        return [
          esc(c.name),
          `${esc(c.owner_name)}<br><small>${esc(c.email)}</small>`,
          esc(a.plan_name),
          badge(a.effective_status),
          esc(a.period_end.slice(0, 10)),
          `${a.shops_used}/${a.max_shops} boutiques · ${a.users_used}/${a.max_users} utilisateurs`,
          `<button data-client-plan="${c.id}">Formule</button> <button data-renew="${c.id}">Renouveler</button> <button data-reset-owner="${c.id}">Réinitialiser l’accès</button> <button data-access="${c.id}">${a.enabled ? "Suspendre" : "Réactiver"}</button>`,
        ];
      }),
      "Entreprises et abonnements",
    )}<div class="table-title" style="padding-inline:0"><h2>Vos formules commerciales</h2><button id="create-plan">＋ Nouvelle formule</button></div>${table(
      [
        "Formule",
        "Prix mensuel MAD",
        "Boutiques maximum",
        "Utilisateurs actifs maximum",
      ],
      state.plans.map((p) => [
        esc(p.name),
        cash(p.price),
        p.max_shops,
        p.max_users,
      ]),
    )}<div style="height:24px"></div>${table(
      [
        "Entreprise",
        "Date",
        "Montant",
        "Durée (mois)",
        "Référence",
        "Période couverte",
      ],
      state.subscription_payments.map((p) => [
        esc(p.company_name),
        esc(p.paid_at.slice(0, 10)),
        cash(p.amount),
        p.months,
        esc(p.reference),
        `${p.period_start.slice(0, 10)} → ${p.period_end.slice(0, 10)}`,
      ]),
      "Historique des abonnements",
    )}<div style="height:24px"></div>${table(
      ["Opération", "Date"],
      state.platform_audit.map((a) => [esc(tr(a.event)), esc(a.date)]),
      "Journal éditeur",
    )}<p class="note">Les règlements d’abonnement sont indépendants des ventes des boutiques. Enregistrez uniquement les paiements effectivement reçus. Les cartes bancaires et prélèvements automatiques ne sont pas activés.</p></main></div>`,
  );
  mountLanguageSwitch();
  $("#logout").onclick = async () => {
    await api("logout", {});
    auth();
  };
  $("#publisher-password").onclick = changePassword;
  $("#create-company").onclick = publisherCompany;
  $("#create-plan").onclick = publisherPlan;
  document.querySelectorAll("[data-client-plan]").forEach(
    (b) =>
      (b.onclick = () => {
        const customer = customers.find((c) => c.id === +b.dataset.clientPlan);
        modal(
          "Changer de formule",
          field(
            "plan_id",
            "Formule",
            "select",
            customer.subscription.plan_id,
            state.plans.filter((p) => p.active).map((p) => [p.id, p.name]),
          ),
          (d) =>
            api("platform/plan", {
              company_id: customer.id,
              plan_id: +d.plan_id,
            }),
        );
      }),
  );
  document.querySelectorAll("[data-reset-owner]").forEach(
    (b) =>
      (b.onclick = () => {
        const customer = customers.find((c) => c.id === +b.dataset.resetOwner);
        modal(
          "Réinitialiser l’accès",
          `<p>${esc(customer.email)}</p><p class="note">Le mot de passe provisoire devra être changé par le client. Ses sessions seront révoquées.</p>${field("password", "Mot de passe provisoire (12 caractères)", "password")}`,
          (d) =>
            api("platform/reset-owner", {
              company_id: customer.id,
              owner_id: customer.owner_id,
              password: d.password,
            }),
        );
      }),
  );
  document
    .querySelectorAll("[data-renew]")
    .forEach(
      (b) =>
        (b.onclick = () =>
          publisherRenew(customers.find((c) => c.id === +b.dataset.renew))),
    );
  document.querySelectorAll("[data-access]").forEach(
    (b) =>
      (b.onclick = () => {
        const customer = customers.find((c) => c.id === +b.dataset.access);
        modal(
          customer.subscription.enabled
            ? "Suspendre l’accès"
            : "Réactiver l’accès",
          `<p>${esc(customer.name)}</p><p class="note">Les données sont conservées. Le contrôle est appliqué à chaque requête, y compris pour les sessions déjà ouvertes. Réactiver un compte ne prolonge pas son abonnement.</p>`,
          () =>
            api("platform/access", {
              company_id: customer.id,
              enabled: !customer.subscription.enabled,
            }),
          "Confirmer",
        );
      }),
  );
}
function publisherCompany() {
  modal(
    "Créer une entreprise cliente",
    `<p class="note">Un compte administrateur et une première boutique seront créés. Le client devra remplacer le mot de passe provisoire à sa première connexion. L’essai dure 14 jours ; aucun paiement n’est supposé reçu.</p><div class="form-grid">${field("company_name", "Nom de l’entreprise")}${field("shop_name", "Nom de la boutique principale")}${field("owner_name", "Nom de l’administrateur client")}${field("email", "E-mail", "email")}${field("password", "Mot de passe provisoire (12 caractères)", "password")}${field(
      "plan_id",
      "Formule",
      "select",
      1,
      state.plans.filter((p) => p.active).map((p) => [p.id, p.name]),
    )}${field("address", "Adresse")}</div>`,
    (d) => api("platform/companies", { ...d, plan_id: +d.plan_id }),
  );
}
function publisherPlan() {
  modal(
    "Créer une formule",
    `<p class="note">Prix mensuel en MAD. Aucun tarif commercial n’est imposé : définissez vos propres montants et limites.</p><div class="form-grid">${field("name", "Nom de la formule")}${field("price", "Prix mensuel MAD", "number")}${field("max_shops", "Boutiques maximum", "number", 1)}${field("max_users", "Utilisateurs actifs maximum", "number", 5)}</div>`,
    (d) => api("platform/plans", d),
  );
}
function publisherRenew(customer) {
  const a = customer.subscription,
    key = crypto.randomUUID();
  modal(
    "Enregistrer un paiement d’abonnement",
    `<p><b>${esc(customer.name)}</b> · ${esc(a.plan_name)}</p><p class="note">Le montant doit correspondre au tarif de la formule multiplié par la durée. La période est prolongée depuis l’échéance existante, ou depuis aujourd’hui si elle est dépassée. Une suspension manuelle reste en place jusqu’à sa réactivation.</p><div class="form-grid">${field("months", "Durée (mois)", "number", 1)}${field("amount", "Montant reçu (MAD)", "number", a.price / 100)}${field("reference", "Référence unique du règlement")}${field(
      "method",
      "Moyen de paiement",
      "select",
      "bank_transfer",
      [
        ["bank_transfer", "Virement bancaire"],
        ["cash", "Espèces"],
        ["other", "Autre"],
      ],
    )}</div>`,
    (d) => api("platform/payment", { ...d, company_id: customer.id, key }),
  );
  $("#f-months").oninput = (e) =>
    ($("#f-amount").value = ((+e.target.value * a.price) / 100).toFixed(2));
}
function changePassword(required = false) {
  modal(
    "Changer mon mot de passe",
    `<p class="note">Choisissez un mot de passe personnel d’au moins 12 caractères. Les autres sessions seront déconnectées.</p>${field("current_password", "Mot de passe actuel", "password")}${field("new_password", "Nouveau mot de passe", "password")}`,
    (d) => api("account/password", d),
  );
  if (required) {
    $("#cancel-modal").hidden = true;
    $("#close-modal").hidden = true;
    $("#modal").oncancel = (e) => e.preventDefault();
  } else $("#modal").oncancel = null;
}
function accountGate() {
  const password = state.password_required;
  $("#app").innerHTML = BazarI18n.html(
    `<div class="account-gate"><header class="topbar"><div class="brand" style="padding:0"><span class="logo">b</span>bazar</div><div class="top-right"><button id="logout">Déconnexion</button></div></header><main><section class="panel"><h1>${password ? "Sécurisez votre compte" : "Votre accès est en pause"}</h1><p>${password ? "Remplacez votre mot de passe provisoire pour accéder à votre espace." : "Votre abonnement est suspendu ou arrivé à échéance. Contactez votre fournisseur pour renouveler votre accès."}</p>${password ? '<button class="primary" id="required-password">Choisir mon mot de passe</button>' : `<p class="note">${esc(state.company)} · ${esc(statusLabel(state.subscription.effective_status))}</p>`}</section></main></div>`,
  );
  mountLanguageSwitch();
  $("#logout").onclick = async () => {
    await api("logout", {});
    $("#modal").close();
    auth();
  };
  if (password) $("#required-password").onclick = () => changePassword(true);
}
function subscriptionPage() {
  const a = state.subscription;
  return `<section class="panel"><div class="panel-head"><h2>Votre abonnement</h2>${badge(a.effective_status)}</div><div class="cards"><div><span class="subtitle">Formule</span><h3>${esc(a.plan_name)}</h3></div><div><span class="subtitle">Prix mensuel MAD</span><h3>${cash(a.price)}</h3></div><div><span class="subtitle">Échéance</span><h3>${esc(a.period_end.slice(0, 10))}</h3></div><div><span class="subtitle">Utilisation</span><h3>${a.shops_used}/${a.max_shops} boutiques</h3><span>${a.users_used}/${a.max_users} utilisateurs</span></div></div><p class="note">Pour changer de formule ou renouveler votre abonnement, contactez votre fournisseur. Les règlements sont validés par l’éditeur après réception du paiement.</p></section><div style="height:24px"></div>${table(
    ["Date", "Montant", "Durée (mois)", "Référence"],
    state.subscription_payments.map((p) => [
      esc(p.paid_at.slice(0, 10)),
      cash(p.amount),
      p.months,
      esc(p.reference),
    ]),
    "Mes règlements d’abonnement",
  )}`;
}
