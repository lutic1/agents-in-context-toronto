# Tavily terms and DxP's "open data only" rule

Read on 12 November 2026 from https://www.tavily.com/terms (Platform Terms of Service, last updated 4 May 2026) and https://www.tavily.com/acceptable-use-policy (last updated 21 October 2026). This is a developer's reading, not legal advice.

## What the terms say

- **"Output"** (section 1.6) is whatever the service returns: text, information and links. Section 1.7 says the Services do not include Output.
- **No rights are granted in returned page content.** Section 9 covers who owns what: the customer owns its input, Tavily owns the Services. It says nothing that gives the customer rights in third-party page content.
- **No warranty that returned content is lawful to reuse.** Section 13.2: Outputs "may be based on publicly available data" over which Tavily has no control, may be "potentially infringing", are provided as is, and the customer is "solely responsible for independently vetting, evaluating, and using the Output".
- **The customer must verify Output** before relying on it or publishing it (section 6.4).
- **Tavily may keep queries and outputs.** Section 6.5 lets Tavily and its AI providers retain inputs and outputs to improve their models. Section 9.2 grants Tavily a broad licence over customer input. The docs mention Zero Data Retention as a setting an account or organisation can have enabled; it is not described as the default.
- **Use is for the customer's internal business purposes**, including inside the customer's own application (section 3.2).
- **Healthcare.** Section 3.2 (xvi) bars automated decisions without human oversight that significantly affect individual rights in high-risk areas, healthcare included. The Acceptable Use Policy bars using outputs about an identifiable individual to decide that person's access to healthcare.
- **Third-party rights.** The Acceptable Use Policy bars using the Services or Outputs to infringe third-party intellectual property, or in a way that breaches a contract the customer owes a third party.
- **Beta features** are provided as is and can be withdrawn (section 3.6). `include_published_date` is marked beta in the API reference.

## What the terms and docs do not say

- Nothing on caching or storing returned content: no time limit, no ban, no permission.
- Nothing that says Tavily excludes paywalled, licensed or login-only pages.
- Nothing that says Extract or Crawl honour robots.txt. The crawl best-practices page tells the caller to "respect robots.txt and site policies".

## What follows for DxP

1. The open-data rule is DxP's to enforce. Ingest only from an allow-list of approved provider domains, and check every URL in code (`host_allowed` in SKILL.md).
2. Storing the page text as the Source item is not restricted by Tavily's terms. Each provider's own website terms still apply, so keep to public marketing, product and press pages, and keep the URL and fetch time with every stored text.
3. Do not ingest a page that needs a login or sits behind a paywall, even if Tavily returns text for it. Congress abstracts and posters stay out (PRD section 6.2).
4. Put nothing confidential, and no personal data, in a query.
5. DxP gives no advice about individual patients and every change goes through a Reviewer, which keeps it clear of the healthcare clauses. Keep it that way.
