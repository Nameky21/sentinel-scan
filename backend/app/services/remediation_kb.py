"""Curated remediation guidance keyed by ZAP plugin id.

ZAP ships its own `solution` text with every alert, but it is generic and often
terse. These entries add targeted, actionable guidance for the findings that
show up most often; anything not covered here falls back to ZAP's own text.
"""

REMEDIATION_KB: dict[str, dict[str, str]] = {
    "40018": {
        "title": "SQL Injection",
        "remediation": (
            "Replace string-concatenated SQL with parameterised queries or prepared statements so user input is "
            "never parsed as SQL. Where an ORM is available, use its query builder rather than raw SQL. Validate "
            "and allow-list any input that must reach the query structurally (table/column names, sort direction), "
            "and run the application's database user with least privilege so a successful injection cannot read or "
            "modify unrelated data."
        ),
        "references": "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html",
    },
    "40012": {
        "title": "Cross-Site Scripting (Reflected)",
        "remediation": (
            "Context-encode all untrusted data on output (HTML body, attribute, JavaScript, URL and CSS contexts "
            "each need different encoding) rather than filtering on input. Use a template engine with automatic "
            "contextual escaping and avoid sinks like innerHTML, document.write and eval. Add a strict "
            "Content-Security-Policy as defence in depth so injected script cannot execute."
        ),
        "references": "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html",
    },
    "40014": {
        "title": "Cross-Site Scripting (Persistent)",
        "remediation": (
            "Stored XSS is higher impact than reflected because the payload is served to every visitor. Encode on "
            "output in the correct context, and sanitise rich-text input server-side with a vetted allow-list "
            "sanitiser (e.g. DOMPurify server-side equivalents) before persisting it. Audit existing stored data "
            "for payloads already saved."
        ),
        "references": "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html",
    },
    "40016": {
        "title": "Cross-Site Scripting (Persistent)",
        "remediation": (
            "Encode untrusted data on output in the correct context and sanitise any rich-text input server-side "
            "with an allow-list sanitiser before storing it. Add a strict Content-Security-Policy as defence in depth."
        ),
        "references": "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html",
    },
    "90020": {
        "title": "Remote OS Command Injection",
        "remediation": (
            "Avoid shelling out entirely where a native library call will do. If a subprocess is unavoidable, pass "
            "arguments as an array (never a concatenated shell string), disable shell interpretation, and "
            "allow-list the permitted commands and argument values. Run the process with the lowest privileges "
            "that still let it do its job."
        ),
        "references": "https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html",
    },
    "90019": {
        "title": "Server-Side Code Injection",
        "remediation": (
            "Never pass user-controlled data to dynamic evaluation functions (eval, exec, deserialisation of "
            "untrusted input, template rendering of user strings). Where dynamic behaviour is genuinely required, "
            "drive it from a fixed allow-list of server-defined options keyed by an opaque identifier."
        ),
        "references": "https://owasp.org/www-community/attacks/Code_Injection",
    },
    "6": {
        "title": "Path Traversal",
        "remediation": (
            "Do not build filesystem paths from user input. Map user-supplied identifiers to server-side paths via "
            "a lookup table, or canonicalise the resolved path and verify it stays inside the intended base "
            "directory before opening it. Reject inputs containing path separators or traversal sequences."
        ),
        "references": "https://owasp.org/www-community/attacks/Path_Traversal",
    },
    "10202": {
        "title": "Absence of Anti-CSRF Tokens",
        "remediation": (
            "Protect every state-changing request with a synchroniser token tied to the user's session, or rely on "
            "the double-submit cookie pattern. Set session cookies to SameSite=Lax or Strict so they are not sent "
            "on cross-site requests, and verify the Origin header on sensitive endpoints."
        ),
        "references": "https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html",
    },
    "10038": {
        "title": "Content Security Policy Header Not Set",
        "remediation": (
            "Add a Content-Security-Policy response header. Start from a restrictive base such as "
            "\"default-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'\" and use nonces or "
            "hashes rather than 'unsafe-inline' for scripts. Deploy in report-only mode first to find breakage "
            "before enforcing."
        ),
        "references": "https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html",
    },
    "10020": {
        "title": "Missing Anti-clickjacking Header",
        "remediation": (
            "Send \"Content-Security-Policy: frame-ancestors 'none'\" (or 'self' if the app frames itself) to stop "
            "the page being embedded in an attacker's iframe. X-Frame-Options: DENY covers older browsers but is "
            "superseded by frame-ancestors."
        ),
        "references": "https://cheatsheetseries.owasp.org/cheatsheets/Clickjacking_Defense_Cheat_Sheet.html",
    },
    "10021": {
        "title": "X-Content-Type-Options Header Missing",
        "remediation": (
            "Send \"X-Content-Type-Options: nosniff\" on every response so browsers honour the declared "
            "Content-Type instead of MIME-sniffing it, which can turn an uploaded file into executable script. "
            "Also make sure Content-Type is set correctly and includes a charset for text responses."
        ),
        "references": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Content-Type-Options",
    },
    "10035": {
        "title": "Strict-Transport-Security Header Not Set",
        "remediation": (
            "Serve the site over HTTPS only and add "
            "\"Strict-Transport-Security: max-age=31536000; includeSubDomains\" so browsers refuse to fall back to "
            "HTTP. Redirect all HTTP traffic to HTTPS, and consider preload submission once the policy is proven "
            "stable across every subdomain."
        ),
        "references": "https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Strict_Transport_Security_Cheat_Sheet.html",
    },
    "10063": {
        "title": "Permissions Policy Header Not Set",
        "remediation": (
            "Add a Permissions-Policy header disabling browser features the app does not use, e.g. "
            "\"geolocation=(), camera=(), microphone=(), payment=()\". This limits what injected or embedded "
            "third-party content can request from the user."
        ),
        "references": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Permissions-Policy",
    },
    "10010": {
        "title": "Cookie Without HttpOnly Flag",
        "remediation": (
            "Set HttpOnly on session and other security-relevant cookies so client-side JavaScript cannot read "
            "them, which blunts session theft via XSS. Cookies genuinely required by front-end code should be "
            "split out and must not carry authentication value."
        ),
        "references": "https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html",
    },
    "10011": {
        "title": "Cookie Without Secure Flag",
        "remediation": (
            "Set the Secure attribute on all cookies so they are only transmitted over HTTPS and never leak over a "
            "plaintext connection. Pair this with HSTS so the browser does not attempt HTTP in the first place."
        ),
        "references": "https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html",
    },
    "10054": {
        "title": "Cookie Without SameSite Attribute",
        "remediation": (
            "Set SameSite=Lax (or Strict for purely first-party session cookies) so cookies are not attached to "
            "cross-site requests, mitigating CSRF. Only use SameSite=None for cookies that genuinely need "
            "cross-site delivery, and always pair it with Secure."
        ),
        "references": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite",
    },
    "90033": {
        "title": "Loosely Scoped Cookie",
        "remediation": (
            "Scope cookies to the exact host that needs them rather than a parent domain. A cookie set on "
            ".example.com is sent to every subdomain, so one compromised or untrusted subdomain can read or "
            "overwrite it."
        ),
        "references": "https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html",
    },
    "10098": {
        "title": "Cross-Domain Misconfiguration",
        "remediation": (
            "Do not reflect arbitrary Origin values or send \"Access-Control-Allow-Origin: *\" alongside "
            "credentials. Maintain an explicit allow-list of trusted origins, echo only matching values, and keep "
            "Access-Control-Allow-Credentials off unless cross-origin authenticated access is genuinely required."
        ),
        "references": "https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html#cross-origin-resource-sharing",
    },
    "10017": {
        "title": "Cross-Domain JavaScript Source File Inclusion",
        "remediation": (
            "Self-host third-party scripts where practical. If a CDN must be used, pin the exact version and add "
            "Subresource Integrity (integrity + crossorigin attributes) so a tampered file will not execute, and "
            "restrict script-src in your CSP to the specific trusted hosts."
        ),
        "references": "https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity",
    },
    "10036": {
        "title": "Server Leaks Version Information",
        "remediation": (
            "Suppress or genericise the Server header at the web server or reverse proxy. Version banners let an "
            "attacker match your stack against known CVEs without probing. This is low risk on its own but removes "
            "free reconnaissance."
        ),
        "references": "https://owasp.org/www-project-web-security-testing-guide/",
    },
    "10037": {
        "title": "Server Leaks Information via X-Powered-By",
        "remediation": (
            "Remove the X-Powered-By header (and framework equivalents such as X-AspNet-Version) in the "
            "application or at the reverse proxy so the technology stack and version are not advertised."
        ),
        "references": "https://owasp.org/www-project-web-security-testing-guide/",
    },
    "90022": {
        "title": "Application Error Disclosure",
        "remediation": (
            "Return generic error pages to clients and log full stack traces server-side only. Disable debug mode "
            "in production — verbose errors expose file paths, framework versions, SQL fragments and internal "
            "logic that make further attacks much cheaper."
        ),
        "references": "https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html",
    },
    "10023": {
        "title": "Information Disclosure - Debug Error Messages",
        "remediation": (
            "Turn off debug output in production builds and route detailed diagnostics to server-side logs. "
            "Review error handlers so unexpected exceptions cannot bubble raw messages back to the client."
        ),
        "references": "https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html",
    },
    "10027": {
        "title": "Information Disclosure - Suspicious Comments",
        "remediation": (
            "Strip developer comments (TODO, FIXME, credentials, internal URLs, ticket references) from client-side "
            "assets during the production build. Minifiers can remove comments automatically; make it part of the "
            "build pipeline rather than a manual step."
        ),
        "references": "https://owasp.org/www-project-web-security-testing-guide/",
    },
    "10015": {
        "title": "Re-examine Cache-control Directives",
        "remediation": (
            "Send \"Cache-Control: no-store\" on responses containing personal or authenticated data so it is not "
            "written to disk by browsers or shared caches. Static, non-sensitive assets should be cached "
            "aggressively with immutable, fingerprinted URLs."
        ),
        "references": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control",
    },
    "10096": {
        "title": "Timestamp Disclosure",
        "remediation": (
            "Usually informational. Confirm the disclosed values are not internal build times, session identifiers "
            "or predictable seeds used for tokens; predictable time-based values can make token guessing feasible."
        ),
        "references": "https://owasp.org/www-project-web-security-testing-guide/",
    },
    "40035": {
        "title": "Hidden File Found",
        "remediation": (
            "Remove version control directories, backups, environment files and editor artefacts from the web root, "
            "and configure the server to deny requests for dotfiles and known sensitive paths. Treat any secret "
            "that was exposed this way as compromised and rotate it."
        ),
        "references": "https://owasp.org/www-project-web-security-testing-guide/",
    },
    "40003": {
        "title": "CRLF Injection",
        "remediation": (
            "Strip or reject carriage return and line feed characters in any user input that reaches a response "
            "header, log line or redirect target. Prefer framework APIs that set headers structurally instead of "
            "building header strings by concatenation."
        ),
        "references": "https://owasp.org/www-community/vulnerabilities/CRLF_Injection",
    },
}


def lookup(plugin_id: str | None) -> dict[str, str] | None:
    if not plugin_id:
        return None
    return REMEDIATION_KB.get(str(plugin_id))


def remediation_for(plugin_id: str | None, zap_solution: str | None) -> tuple[str, bool]:
    """Return (remediation_text, is_curated). Falls back to ZAP's own solution text."""
    entry = lookup(plugin_id)
    if entry:
        return entry["remediation"], True
    return (zap_solution or "No remediation guidance available for this finding."), False
