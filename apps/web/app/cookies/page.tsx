export const metadata = {
  title: "Cookie Policy — TideGuard AI",
};

export default function CookiesPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-12 prose">
      <h1>Cookie Policy</h1>
      <p>
        <strong>Last updated:</strong> 2026-05-23 · <strong>Version:</strong> 0.4.0
      </p>

      <h2>What cookies we set</h2>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Purpose</th>
            <th>Type</th>
            <th>Expires</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <code>tideguard_jwt</code>
            </td>
            <td>Holds the JSON Web Token for authenticated requests.</td>
            <td>strictly-necessary, HttpOnly, Secure, SameSite=Lax</td>
            <td>24 h</td>
          </tr>
          <tr>
            <td>
              <code>tideguard_csrf</code>
            </td>
            <td>CSRF double-submit token for state-changing POST/PATCH.</td>
            <td>strictly-necessary, Secure, SameSite=Lax</td>
            <td>session</td>
          </tr>
          <tr>
            <td>
              <code>tideguard_locale</code>
            </td>
            <td>Stores user-selected language (ru / en) — RU is default.</td>
            <td>functional</td>
            <td>1 year</td>
          </tr>
        </tbody>
      </table>

      <h2>Third-party trackers</h2>
      <p>
        <strong>None.</strong> No Google Analytics, no Facebook Pixel,
        no advertising or fingerprinting cookies are set by TideGuard.
      </p>

      <h2>How to manage cookies</h2>
      <p>
        You can delete cookies via your browser&apos;s privacy settings; the site
        will continue to function for read-only use.
      </p>
    </main>
  );
}
