export const metadata = {
  title: "Terms of Service — TideGuard AI",
};

export default function TermsPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-12 prose">
      <h1>Terms of Service</h1>
      <p>
        <strong>Last updated:</strong> 2026-05-23 · <strong>Version:</strong> 0.4.0
      </p>

      <h2>1. Service</h2>
      <p>
        TideGuard AI provides forecasts of floating marine debris concentration
        based on a Physics-Informed Neural Network, plus a citizen-science
        reporting interface and a K-12 environmental education module. The
        service is offered free of charge for non-commercial educational and
        research use.
      </p>

      <h2>2. No warranty</h2>
      <p>
        The service is provided <em>as is</em>. TideGuard AI is{" "}
        <strong>not</strong> a navigational aid, a search-and-rescue tool, or
        a substitute for official maritime advisories. Decisions involving
        life-safety must consult the relevant national hydrometeorological
        service.
      </p>

      <h2>3. Acceptable use</h2>
      <p>
        Do not upload illegal content, doxx other users, or attempt to use the
        API to crawl personal information. Automated requests must respect the
        published rate limits (see <a href="/developers">/developers</a>).
      </p>

      <h2>4. Citizen-science reports</h2>
      <p>
        By submitting a report, you grant TideGuard AI a perpetual, irrevocable,
        worldwide, CC-BY-4.0 licence to display the report on the public map and
        re-use it for model training.
      </p>

      <h2>5. Account responsibility</h2>
      <p>
        You are responsible for keeping your account credentials safe. Notify
        us at <a href="mailto:scaleblinkk@vk.com">scaleblinkk@vk.com</a> if
        you suspect your account is compromised.
      </p>

      <h2>6. Open source</h2>
      <p>
        Source code is MIT-licensed; educational content is CC-BY-4.0;
        model artefacts on Zenodo are CC-BY-4.0. See the GitHub repository:
        <a href="https://github.com/BitMagistrate/TideGuard"> tideguard</a>.
      </p>

      <h2>7. Termination</h2>
      <p>
        TideGuard AI may suspend or terminate access for any user violating
        these terms. You may delete your account at any time via{" "}
        <code>DELETE /users/me</code> or by emailing us.
      </p>

      <h2>8. Governing law</h2>
      <p>
        For users in Russia: Russian Federation civil code. For EU users: the
        laws of the user&apos;s habitual residence apply to consumer rights.
      </p>
    </main>
  );
}
