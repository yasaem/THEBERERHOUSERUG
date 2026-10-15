# Bazar — Retail management ERP

[Documentation française](README.md) · **English**

A French/English responsive web application for Moroccan retailers. Python JSON API, SQLite relational database and ReportLab A4 invoices. This version includes publisher administration, customer provisioning, subscription plans and manual payments. Public deployment and automatic billing still require your external accounts, credentials and production acceptance.

## Web preview without your own domain or VPS

[**Deploy the free Render preview**](https://render.com/deploy?repo=https://github.com/yasaem/THEBERERHOUSERUG)

Render provides an HTTPS subdomain after deployment. Sign in, grant repository access if private, verify the Free plan, and enter your publisher email/password in the private deployment fields (never in chat or Git). Full steps: `docs/RENDER_PREVIEW.md`.

**Temporary data only:** free SQLite storage is ephemeral and may be lost on restart/redeployment. A visible banner marks demo mode. Do not use real customer data or sell this preview as a production service. The link opens the deployment form; no live Render URL or resource has been created from this session yet.

## Get the source and start

Python 3.12+ is required. Node.js is only needed for the optional JavaScript syntax check.

```bash
git clone https://github.com/yasaem/THEBERERHOUSERUG.git
cd THEBERERHOUSERUG
./scripts/install.sh
.venv/bin/python server.py
```

On Windows, use the equivalent virtual environment commands (`python -m venv .venv`, `.venv\Scripts\python -m pip install -r requirements.txt`, `.venv\Scripts\python server.py`). The install shell script is intended for Linux/macOS and the cloud environment.

The server listens on **port 3000**. Public registration is closed by default. Run `.venv/bin/python scripts/create_platform_admin.py` in a trusted terminal to create your publisher account (masked password, at least 12 characters). Sign in and provision each customer company, its administrator and first shop. Customers must replace their temporary password at first login and can then manage their shops and users. No default account or password is installed. Data is stored in `.data/bazar.sqlite3` and is not committed to Git.

If a checkout already exists, use it and preserve any local changes before updating.

## French and English

Select **Français / English** on the sign-in page or in the top bar. The browser remembers the choice after reload and sign-out. Navigation, forms, tables, status labels, messages and CSV headings follow this choice. Product descriptions, company/shop names, customers and other business data are preserved exactly as entered.

Open an invoice and use **Invoice language** to choose its language independently. The preview, printed document, PDF, email subject and email body use that choice. Language changes never modify historical amounts, references, tax settings or commission calculations. Currency remains **MAD**.

Interface translations live in `static/translations.json`, rendering helpers in `static/i18n.js`, and explicit PDF labels in `documents.py`. API errors follow the `X-App-Language` header. Document endpoints accept JSON `language: "fr"` or `"en"`; the default is French and unsupported languages are rejected.

## Everyday workflow

1. Add shops and products, or use **Import** in **Products & stock**. CSV UTF-8 and `.xlsx` are supported, first sheet only, up to 1,000 products. Map columns and review the preview before confirmation. Name, reference and a whole-number quantity are required. Duplicate references or invalid rows reject the entire import. A sample is provided in `docs/stock-exemple.csv`.
2. Use **Adjust** to correct stock with a reason, **Edit** to change product details, and archive products to prevent future sales without deleting history.
3. Create a **New sale** with several stocked products and/or custom items. Enter unit prices excluding VAT in MAD, the discount, VAT, shipping cost, bank fees and initial payment.
4. Add commission beneficiaries. Sellers share one commission pool (percentage or fixed amount), with shares totalling 100%. Guides/agencies/drivers have independent commissions. Link a beneficiary to a seller account so they can view their own gains.
5. Confirm the sale. Stock, commissions, initial payment, immutable invoice snapshot and audit trail are recorded transactionally. Repeated submission with the same idempotency key cannot duplicate the sale.
6. Record subsequent customer receipts from **Sales**. Record commission payments separately from **Commissions**. Partial settlements are supported for sales, commissions, expenses and salaries.
7. Open an invoice to preview, choose the document language, print, download an A4 PDF or send it through configured SMTP. Add your legal address, ICE, tax ID and logo in **Settings → Billing information**. New invoices retain this information; old invoices keep their original snapshot.
8. Manage staff and manually declare each salary period from **Employees & salaries**. A reference salary alone does not create a charge. Declare each period once: duplicate salary periods are not automatically blocked and statutory payroll is outside scope.
9. Select a shop and month to review the dashboard and reports. CSV exports use translated headings and display raw monetary amounts in **MAD cents**, clearly labelled; dates use UTC.
10. Owners manage user roles, activation, password resets and assigned shop. Managers see operational and financial data for their assigned shop. Sellers see their sales and gains plus stock without purchase costs. Operators see stock without purchase costs and can add sales.

Cancelling a sale restores stock once and cancels unpaid commissions. Existing receipts remain in the audit history and refunds must be reconciled separately. Already-paid commissions block cancellation pending regularisation. This is not a statutory credit-note workflow.

## Financial assumptions

All monetary values are stored as integer MAD cents. Prices exclude VAT. A global discount is deducted before a global VAT rate (0%, 10% or 20%). Commission base is `max(0, discounted amount excl. VAT − shipping cost)`, excluding VAT and without deducting bank fees.

Seller pool allocation uses largest remainders to preserve every cent. Profit subtracts historical goods costs, shipping, bank fees, earned commissions, expenses incurred and salaries owed. Paying a liability does not create a second charge. Do not re-enter sale fees or declared salaries as additional expenses. Unknown custom-item costs default to zero and can therefore overstate estimated profitability.

## Tests

```bash
.venv/bin/python -m unittest discover -s tests -v
node --check static/app.js
node --check static/i18n.js
```

Tests use a temporary database and cover tenant/shop isolation, permissions, financial calculations, commission allocation, stock restoration, idempotency, partial payments, Excel import, immutable invoices, FR/EN PDFs and email composition. Email tests use a mock SMTP server: no external messages are sent. Real provider delivery needs a separate check. The main desktop/mobile browser workflow has also been exercised in Chromium.

## Configuration and email

| Variable | Purpose |
|---|---|
| `HOST` | Bind address; defaults to `0.0.0.0`. Use `127.0.0.1` behind a local proxy. |
| `PORT` | Defaults to `3000`. |
| `BAZAR_DB` | Database path; defaults to `.data/bazar.sqlite3`. |
| `COOKIE_SECURE` | Set to `1` when served over HTTPS. |
| `SMTP_HOST`, `SMTP_PORT` | Outgoing STARTTLS mail server; port 587 by default. |
| `SMTP_FROM` | Authorised sender address. |
| `SMTP_USER`, `SMTP_PASSWORD` | Provider credentials where required. |

Use your hosting secret manager for credentials. The app reads process environment variables and does not automatically load `.env`. SMTP uses mandatory STARTTLS with certificate validation. No external provider delivery has been verified. Sending is synchronous; a queue is recommended before large-scale use.

## Backup and restore

```bash
.venv/bin/python scripts/backup.py --destination /private/backup/directory
```

This creates a consistent SQLite backup and checks integrity, including while the app is running. Schedule it with your hosting scheduler; no recurring task is installed automatically. Encrypt/protect off-machine copies, define retention and test restoration regularly.

To restore: stop the app, retain a copy of the current database, restore the backup at `BAZAR_DB`, protect file permissions, clear restored sessions (`DELETE FROM sessions`), restart and verify login, shops, stock and an invoice. Test restoration separately before relying on backups.

## Deployment and remaining scope

For a private pilot, use a persistent database volume, a process supervisor and an HTTPS reverse proxy with `COOKIE_SECURE=1`, a 2 MB request limit and rate limiting for login/registration. The bundled HTTP server is intended for development and private acceptance testing, not direct public Internet exposure.

Before commercial launch, complete Moroccan tax/legal validation, independent security review, operational monitoring, external backups and load testing. EUR/USD and historical exchange rates, custom permissions, multiple assigned shops per non-owner account, partial returns/credit notes, customer-billed delivery, configurable tax rates, automatic subscription billing and transfers remain to be implemented. Lists currently load in full without server-side pagination. There is no Arabic UI or offline mode. Customer records are not yet relationally linked to sales. See `docs/RECETTE.md` for the detailed coverage matrix.

Never commit `.data/`, `.venv/`, `.env`, backups or SMTP credentials. These are excluded by `.gitignore`. The application code and documentation are maintained on the GitHub repository's `main` branch.

## Publisher subscriptions

The publisher dashboard is separate from customer ERP data. Create your own plans with monthly MAD pricing, shop quotas and active-user quotas. New companies receive a 14-day trial. Record only transfers/cash payments actually received, with a unique reference. Payments extend coverage by calendar months; they are not automatic card charges. Manual suspension is not removed by a payment and must be explicitly lifted. Expiry, suspension and quotas are enforced by the API, including existing sessions. Restarting the app does not renew trials.

Publishers can reset a customer's administrator access without knowing their current password; sessions are revoked and a new personal password is required. Subscription receipts and shop sales are kept separate. The subscription ledger is not a statutory tax invoice. A merchant provider, verified business account and signed/idempotent webhooks are still required before automatic payments.

See `docs/SAAS.md` for the full publisher workflow (French).

## Persistent deployment with Cloudflare

Cloudflare Tunnel routes HTTPS traffic to a persistent Docker/Gunicorn server; it does not host the Python/SQLite application by itself. Provide a Linux VPS/server that stays on, Docker/Compose, a domain in your Cloudflare account and a remotely managed tunnel. No domain/server purchase or public deployment has been performed.

```bash
cp deploy.env.example .env
chmod 600 .env
# Set your real HTTPS domain and secrets privately.
docker compose build
docker compose up -d app backup
docker compose exec app python scripts/create_platform_admin.py
# After configuring the tunnel token in .env:
docker compose --profile cloudflare up -d
```

Configure the public hostname's tunnel service as `http://app:3000`. `PUBLIC_BASE_URL` must match the real HTTPS origin. Secure cookies remain enabled. The backend port binds only to loopback; do not expose it directly. Do not cache authenticated/API responses. Persistent data and six-hour backups use separate Docker volumes; never run `docker compose down -v`. Off-server encrypted backups, monitoring, legal acceptance and load testing are still required. SQLite WAL supports a single persistent server, not horizontally replicated independent databases.

For local Gunicorn without Docker: `.venv/bin/gunicorn --config gunicorn.conf.py wsgi:application`. The original HTTP server remains development-only. `BAZAR_ALLOW_SIGNUP=1` is an explicit demo/test option and must stay off commercially.

Docker builds in the current environment lacked outbound DNS. The tested alternative downloads wheels over verified HTTPS and then installs offline (no TLS/checksum verification disabled):

```bash
.venv/bin/python -m pip download --only-binary=:all: --dest .build/wheels -r requirements.txt
docker build --build-arg DEPENDENCY_STAGE=offline -t bazar-erp:local .
```

Use wheels matching Python 3.12 and the target platform. Full deployment details and restore procedures are in `docs/CLOUDFLARE.md`.

40 tests passed, also inside Docker. The publisher-to-customer browser workflow, quota enforcement, payment, suspension, restart persistence and backup restoration into a separate database were verified. The official Cloudflare connector image was verified by digest and its binary executed, but no authenticated production tunnel was connected. A GitHub Actions workflow is included; a remote CI run is not claimed without observing it.
