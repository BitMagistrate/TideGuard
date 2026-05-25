export const metadata = {
  title: "Privacy Policy — TideGuard AI",
  description:
    "Privacy policy for the TideGuard AI marine debris forecasting and citizen-science platform.",
};

export default function PrivacyPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-12 prose">
      <h1>Privacy Policy</h1>
      <p>
        <strong>Last updated:</strong> 2026-05-23 · <strong>Version:</strong> 0.4.0
      </p>

      <h2>Who we are</h2>
      <p>
        TideGuard AI is an open-source environmental project operated by Vladimir Yermolenko
        (Gimnasium No. 13 «Academ», Krasnoyarsk, Russia) as a solo non-commercial initiative.
        Contact: <a href="mailto:scaleblinkk@vk.com">scaleblinkk@vk.com</a>.
      </p>

      <h2>What data we collect</h2>
      <ul>
        <li>
          <strong>Citizen-science reports.</strong> Latitude / longitude, timestamp, debris
          severity (1–5), brand / fraction free-text, optional photo. We do <em>not</em>
          require login for a report and we do not store IP addresses next to the report.
        </li>
        <li>
          <strong>Photos.</strong> EXIF (GPS) metadata is stripped server-side
          <em>before</em> persistence; faces are blurred (MediaPipe). The original raw
          image is not retained.
        </li>
        <li>
          <strong>Account info (optional).</strong> Email for login; never sold, never
          shared with third parties.
        </li>
        <li>
          <strong>Analytics.</strong> Page-view counts only; no third-party trackers; no
          fingerprinting; no advertising IDs.
        </li>
      </ul>

      <h2>Why we collect it</h2>
      <p>
        Marine-debris forecasts improve when we have real observations from real
        beaches. Aggregated reports also feed the public <code>/map</code>, the
        <code>/impact</code> page, and the open <code>/cleanups/stats</code> API.
      </p>

      <h2>Where it is stored</h2>
      <p>
        Database: managed Postgres on Fly.io (eu-central). Photos: Cloudflare R2
        (eu). Backups: daily, retained 30 days. We do not transfer data outside
        the EU / Russia regulatory perimeter.
      </p>

      <h2>Legal basis (152-ФЗ and GDPR)</h2>
      <p>
        Russian Federal Law 152-ФЗ Art. 6 §1(7) (legitimate interest in
        environmental protection) and GDPR Art. 6 §1(e) (task carried out in the
        public interest). For minors under 14, GDPR Art. 8 applies — parental
        consent is required and is collected via the school consent forms in
        <code>docs/consent_forms/</code>.
      </p>

      <h2>Your rights</h2>
      <ul>
        <li>
          <strong>Access and export.</strong> Send <code>DELETE /reports</code>{" "}
          via the API with your JWT, or email
          <a href="mailto:scaleblinkk@vk.com"> scaleblinkk@vk.com</a>.
        </li>
        <li>
          <strong>Erasure.</strong> Same as above — your reports and any linked
          account will be hard-deleted within 30 days.
        </li>
        <li>
          <strong>Portability.</strong> All your data is exposed via the public REST API
          in machine-readable form.
        </li>
        <li>
          <strong>Complaint.</strong> Russian Roskomnadzor or your local EU DPA.
        </li>
      </ul>

      <h2>Children&apos;s data</h2>
      <p>
        K-12 lesson pages run entirely client-side and do not collect any data.
        Photo uploads from the educational kit require parental consent collected
        offline.
      </p>

      <h2>Cookies</h2>
      <p>
        See <a href="/cookies">/cookies</a>. We only use technically required cookies
        (session, JWT, CSRF). No tracking pixels.
      </p>

      <h2>Changes</h2>
      <p>
        We will keep an open changelog of this page in the public
        <a href="https://github.com/BitMagistrate/TideGuard"> GitHub repo</a>.
      </p>
    </main>
  );
}
