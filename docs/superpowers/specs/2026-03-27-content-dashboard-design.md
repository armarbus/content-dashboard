# Content Dashboard — Design Spec
**Datum:** 2026-03-27
**Eigenaar:** Ayman (Hybrid Performance Coach)
**Status:** Goedgekeurd door gebruiker

---

## 1. Doel

Een geautomatiseerd content research dashboard dat wekelijks viral Instagram Reels van 6 concurrenten analyseert. Ayman opent elke ochtend één URL en ziet direct welke hooks, thema's en formats viral gaan — inclusief een AI-suggestie hoe hij het zelf kan flippen voor zijn hybrid performance merk.

**Kernbelofte:** Van viral content zien → eigen Short idee hebben in < 2 minuten.

---

## 2. Stack

| Component | Keuze | Reden |
|---|---|---|
| Frontend / UI | Streamlit (Python) | Gratis hosting, snel itereerbaar |
| Database | Supabase (PostgreSQL) | Gratis tier, eenvoudige API |
| Scraping | Apify — Instagram Reel Scraper | Meest betrouwbaar, pay-per-use |
| AI Analyse | OpenAI GPT-4o-mini | Goedkoop, snel, goed genoeg |
| Hosting | Streamlit Cloud | Gratis, altijd bereikbaar |
| Automatisering | GitHub Actions (cron, gratis) | Betrouwbaar, secrets veilig opgeslagen |

**Geschatte kosten:** €8–10/maand (Apify ~€5 + OpenAI ~€3–5)

---

## 3. Data Bronnen

**Platform:** Instagram Reels (only)

**Eigen account:**
- @aymanraoul (apart weergegeven in "Mijn Performance" tab)

**Concurrenten:**
- @williamdurnik
- @chrismouton_
- @harleysshields
- @kvnramirezz
- @alexmegino
- @kirstyhendey

**Scraping frequentie:** Wekelijks (elke maandag 06:00)
**Volume per run:** Laatste 10 Reels per account = max 70 videos/week (6 concurrenten + eigen account)

**Veld `is_own_account`** (boolean) toegevoegd aan `reels` tabel om onderscheid te maken tussen eigen content en concurrenten.

---

## 4. Data Model

Tabel: `reels`

| Kolom | Type | Beschrijving |
|---|---|---|
| reel_id | text | **Primary key** — Instagram shortcode (uniek, stabiel) |
| is_own_account | boolean | True als het @aymanraoul is, False voor concurrenten |
| scraped_at | timestamp | Wanneer gescraped |
| competitor_handle | text | Zonder @-prefix, bijv. `williamdurnik` |
| video_url | text | Directe link naar Reel |
| thumbnail_url | text | Preview afbeelding |
| caption | text | Originele caption |
| hook | text | Eerste 6–8 woorden (AI geëxtraheerd, zie §7) |
| hook_type | text | Label: identiteit / tegenstelling / discipline / transformatie / lifestyle / anders |
| theme | text | Label: hybrid / voeding / mindset / kracht / lifestyle / anders |
| views | integer | Aantal views |
| likes | integer | Aantal likes |
| comments | integer | Aantal comments |
| posted_at | timestamp | Originele postdatum |
| viral_score | integer | 0–100, berekend (zie §6) |
| ai_why | text | AI-analyse: waarom werkt dit? (1–2 zinnen) |
| ai_your_version | text | AI-suggestie voor Aymanʼs eigen versie |
| week_start_date | date | Maandag van de scrape-week (bijv. 2026-03-23) |

**Upsert key:** `reel_id` (Instagram shortcode uit Apify output). Hiermee worden duplicaten voorkomen bij herhaalde scrapes.

**Conventie handles:** altijd zonder `@`-prefix opgeslagen.

Tabel: `summaries`

| Kolom | Type | Beschrijving |
|---|---|---|
| week_start_date | date | **Primary key** — Maandag van de week |
| generated_at | timestamp | Wanneer gegenereerd |
| trending_themes | text | AI-samenvatting trending thema's |
| best_hook_types | text | Welke hook-types het best werkten |
| top3_to_copy | text | Top 3 aanbevelingen voor Ayman |
| weekly_advice | text | Aanbeveling voor content deze week |

---

## 5. Architectuur & Data Flow

```
GitHub Actions Cron (elke maandag 06:00)
    → Python Processor (draait in GitHub Actions runner)
        → Apify API aanroepen per account (6x)
            → Viral Score berekenen
            → OpenAI: hook extraheren + type labelen + theme labelen + ai_why + ai_your_version
            → Supabase: upsert record (op reel_id)
        → Weekly Summary genereren (OpenAI) → Supabase summaries tabel
            → Streamlit Dashboard (leest uit Supabase bij openen)
```

**Python Processor** draait als GitHub Actions workflow (`.github/workflows/weekly_scrape.yml`). Dit is gratis, betrouwbaar en makkelijk te debuggen via de GitHub Actions logs. Secrets (Apify key, OpenAI key, Supabase key) staan als GitHub repository secrets.

---

## 6. Viral Score Berekening

Relatieve score per concurrent (0–100) gebaseerd op hoe een video presteert *ten opzichte van het gemiddelde* van die account. Dit is beter dan absolute drempels omdat de 6 accounts verschillende publieksgroottes hebben.

```python
def viral_score(views, likes, comments, days_since_posted, avg_views_for_handle):
    # Relatieve views: hoe ver boven/onder gemiddelde?
    view_ratio = views / max(avg_views_for_handle, 1)
    view_score = min(70, view_ratio * 35)  # Max 70 punten, 2x gemiddelde = 70

    # Engagement rate
    engagement = (likes + comments * 2) / max(views, 1)
    engagement_score = min(20, engagement * 200)  # Max 20 punten

    # Recency bonus
    recency = max(0, 1 - (days_since_posted / 14))
    recency_score = recency * 10  # Max 10 punten

    return min(100, int(view_score + engagement_score + recency_score))
```

`avg_views_for_handle` wordt berekend als het gemiddelde van de laatste 20 Reels van die account in de database.

Score 0–100. Grens voor "viral" filter in het dashboard: ≥ 60.

---

## 7. AI Analyse (OpenAI Prompt)

Per video wordt één API-call gedaan met de volgende output (JSON):

```json
{
  "hook": "eerste 6-8 woorden van de caption of video-tekst",
  "hook_type": "identiteit | tegenstelling | discipline | transformatie | lifestyle | anders",
  "theme": "hybrid | kracht | voeding | mindset | lifestyle | anders",
  "ai_why": "1-2 zinnen waarom deze video viral gaat in de hybrid/fitness niche",
  "ai_your_version": "concrete hook of idee hoe Ayman dit kan nabouwen voor zijn merk"
}
```

**Hook extractie — fallback logica:**
1. Als er video-tekst/overlay beschikbaar is via Apify → gebruik eerste 6–8 woorden daarvan
2. Als alleen caption beschikbaar is en begint met echte tekst (niet hashtag/emoji) → gebruik eerste 6–8 woorden
3. Als caption leeg is of begint met `#` of emoji → AI genereert een beschrijvende hook op basis van beschikbare metadata
4. Als er niets beschikbaar is → `hook = "Geen tekst beschikbaar"`

**System prompt (meegestuurd bij elke call):**
```
Je bent een content analist voor Ayman, een hybrid performance coach.
Zijn merk: kracht + hardlopen, discipline, stoïcijnse mindset, masculine lifestyle.
Doelgroep: mannen 16–35 die sterker, droger en mentaal scherper willen worden.
Merkboodschap: "Bouw een hybride lichaam. Bouw discipline. Bouw jezelf."
Zijn eigen hook-stijl: identiteit ("mannen die trainen winnen"), tegenstelling
("stop met alleen bulken"), discipline ("je hoeft je niet goed te voelen om te winnen"),
lifestyle ("sober living, early mornings, consistent training").
Analyseer de aangeleverde Instagram Reel en geef output als JSON.
```

---

## 8. Dashboard — 5 Tabs

### Tab 1: 🔥 Viral Content Overview
- Top 10 Reels van deze week (alle concurrenten, gesorteerd op Viral Score)
- Kolommen: Thumbnail | Hook | Creator | Thema | Views | Score | Waarom | Jouw Versie | Link
- Filter: week selector, viral score drempel (default ≥ 60)

### Tab 2: 👥 Per Concurrent
- Dropdown: kies een account
- Alle Reels van die account, gesorteerd op Viral Score
- Zelfde kolommen als Tab 1

### Tab 3: 🪝 Hook Library
- Alle hooks gegroepeerd op `hook_type`
- Per hook-type: lijst van meest gebruikte hooks + gemiddelde viral score
- Tabel: Hook tekst | Type | Viral Score | Creator | Link

### Tab 4: 💡 Value Content Library
- Alle Reels gegroepeerd op `theme`
- Filter op thema (hybrid, kracht, voeding, mindset, lifestyle)
- Tabel: Hook | Creator | Views | Score | Jouw Versie | Link

### Tab 5: 📈 Mijn Performance
- Alle Reels van @aymanraoul gesorteerd op Viral Score
- Grafiek: viral score over tijd (groei zichtbaar maken)
- Kolommen: Thumbnail | Hook | Views | Likes | Score | Datum | Link
- Vergelijking: jouw gemiddelde viral score vs gemiddelde van concurrenten

### Tab 6: 📋 Weekly Summary
- Auto-gegenereerde samenvatting (OpenAI) van de week:
  - Trending thema's
  - Best werkende hook-types
  - Top 3 video's om na te maken
  - Aanbeveling voor Ayman's content deze week

---

## 9. Filters (globaal beschikbaar)

- Week selector (default: huidige week)
- Viral score drempel (slider, default 60)
- Per concurrent (multiselect)
- Hook type (multiselect)
- Thema (multiselect)

---

## 10. Automatisering

| Stap | Tool | Frequentie |
|---|---|---|
| Scrapen + verwerken + AI analyse | GitHub Actions cron | Elke maandag 06:00 |
| Opslaan in database | Supabase upsert op `reel_id` | Direct na verwerking |
| Weekly Summary genereren | OpenAI (einde van run) | Elke maandag na scrape |
| Dashboard refresht | Streamlit (auto bij openen) | Elke keer dat je het opent |

**GitHub Actions workflow:** `.github/workflows/weekly_scrape.yml`
**Secrets:** `APIFY_API_TOKEN`, `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`

## 11. Beveiliging (Supabase)

- Streamlit app gebruikt de Supabase `anon` key (read-only toegang)
- Row Level Security (RLS) ingeschakeld op `reels` en `summaries` tabellen
- Policy: `anon` rol mag alleen SELECT uitvoeren
- Python processor (GitHub Actions) gebruikt de `service_role` key (write toegang), nooit blootgesteld in de frontend

---

## 12. Wat er NIET in zit (bewust weggelaten)

- Geen TikTok of YouTube scraping (scope: Instagram only)
- Geen audio/sound tracking (niet betrouwbaar beschikbaar via Apify)
- Geen volledige captions (te veel ruis)
- Geen email alerts (niet nodig, wekelijks checken is genoeg)
- Geen team-functionaliteit (solo gebruik)

---

## 13. Success Criteria

- Dashboard laadt in < 5 seconden
- Wekelijkse update draait zonder handmatig ingrijpen
- Per video: link, thumbnail, hook, viral score en "jouw versie" zichtbaar
- Ayman kan binnen 2 minuten 3 content-ideeën hebben voor die week
