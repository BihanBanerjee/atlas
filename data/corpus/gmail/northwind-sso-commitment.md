---
id: gmail-northwind-sso-commitment
source: gmail
type: thread
tier: signal
load_bearing: true
subject: "Q3 planning + enterprise requirements"
thread_id: t-0847
date: 2026-06-11
date_range: 2026-06-09..2026-06-11
participants:
  - Marcus Oyelaran <marcus@tensile.dev>
  - Linda Marsh <linda.marsh@northwindlogistics.com>
  - Ravi Menon <ravi@tensile.dev>
facts:
  - SAML SSO promised to Northwind for 2026-09-15
  - Ravi Menon CC'd from the second message — the CEO was aware
  - Audit log export also committed, for end of August
  - Northwind renewal is 2026-09-30; access audit the week prior
---

## Message 1 — 9 June 2026, 10:42

**From:** Linda Marsh <linda.marsh@northwindlogistics.com>
**To:** Marcus Oyelaran <marcus@tensile.dev>
**Subject:** Q3 planning + enterprise requirements

Marcus,

Following up on our call last week. I've been through the security review with our IT group and there are a couple of things I need to flag before we get to the renewal conversation.

The main one: we're consolidating identity onto Okta across the whole org by the end of Q3. Anything that can't do SAML gets written up in the quarterly access audit, and I'd rather Tensile not be on that list. Right now my team is on individual logins, which will fail it.

Second, smaller — we need audit log export. Compliance wants twelve months of retention and a way to pull it themselves.

Where does SAML sit for you? I need something I can put in front of our CTO before renewal comes around.

Linda Marsh
VP Engineering, Northwind Logistics

---

## Message 2 — 10 June 2026, 09:15

**From:** Marcus Oyelaran <marcus@tensile.dev>
**To:** Linda Marsh <linda.marsh@northwindlogistics.com>
**Cc:** Ravi Menon <ravi@tensile.dev>
**Subject:** Re: Q3 planning + enterprise requirements

Linda,

Thanks for laying it out that clearly, it helps.

Audit log export is the straightforward one — already scoped, and I can get you a date this week.

On SAML, let me check sequencing with Dana before I give you a number. Adding Ravi here, he's closer to the roadmap than I am.

One question so I scope it properly: is Okta the only IdP you need, or should we be thinking about Azure AD for the wider group as well?

Marcus Oyelaran
Head of Sales, Tensile
tensile.dev

---

## Message 3 — 10 June 2026, 14:03

**From:** Linda Marsh <linda.marsh@northwindlogistics.com>
**To:** Marcus Oyelaran <marcus@tensile.dev>
**Cc:** Ravi Menon <ravi@tensile.dev>
**Subject:** Re: Q3 planning + enterprise requirements

Okta only — the rest of the group sits on the same tenant.

To be direct about timing. Our renewal is 30 September and the access audit runs the week before it. If SAML isn't live by then I'm either requesting an exception or moving the team to something that supports it, and I don't want to do either.

Linda

---

## Message 4 — 11 June 2026, 11:27

**From:** Marcus Oyelaran <marcus@tensile.dev>
**To:** Linda Marsh <linda.marsh@northwindlogistics.com>
**Cc:** Ravi Menon <ravi@tensile.dev>
**Subject:** Re: Q3 planning + enterprise requirements

Linda,

Spoke with the team. Good news on both counts.

Audit log export with twelve month retention is in the Q3 build, targeting end of August. I'll confirm the exact date once the sprint plan firms up.

On identity — we'll have SAML SSO shipped for you by September 15. That puts you two weeks clear of the audit and ahead of the renewal date.

I'll send a written summary next week that you can take to your CTO.

Marcus Oyelaran
Head of Sales, Tensile
tensile.dev
