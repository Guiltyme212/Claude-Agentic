#!/usr/bin/env python3
"""
HTML email template for AiBoostly cold outreach.

Wraps plain-text email body into a clean, personal HTML design.
The preview URL gets turned into a prominent CTA button.
Keeps the personal "Dan texting you" feel — not a marketing newsletter.

Email HTML rules followed:
- Inline styles only (no <style> blocks — many clients strip them)
- Table-based layout (Outlook compatibility)
- System font stack (no web fonts in email)
- All colors as hex values
- Max width 600px (email standard)
"""

import re


def extract_preview_url(email_body: str) -> str | None:
    """Find the Netlify preview URL in the email body."""
    match = re.search(r'https?://[a-zA-Z0-9._-]+\.netlify\.app\S*', email_body)
    return match.group(0) if match else None


def build_html_email(email_body: str, business_name: str = "") -> str:
    """
    Convert plain-text email body into designed HTML.

    - Extracts the preview URL and turns it into a CTA button
    - Wraps text in clean typography
    - Adds subtle AiBoostly footer
    """
    preview_url = extract_preview_url(email_body)

    # Escape HTML entities in the body
    safe_body = (
        email_body
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    # Replace the preview URL line with a CTA button
    if preview_url:
        safe_url = preview_url.replace("&", "&amp;")
        # Replace the URL (which was escaped) with a button placeholder
        safe_body = safe_body.replace(safe_url, "{{CTA_BUTTON}}")

    # Convert newlines to HTML, splitting into paragraphs on double newlines
    paragraphs = safe_body.split("\n\n")
    html_paragraphs = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if "{{CTA_BUTTON}}" in p:
            # This paragraph contains the CTA — split around it
            parts = p.split("{{CTA_BUTTON}}")
            before = parts[0].strip().replace("\n", "<br>")
            after = parts[1].strip().replace("\n", "<br>") if len(parts) > 1 else ""

            if before:
                html_paragraphs.append(
                    f'<p style="margin:0 0 16px 0;font-size:15px;line-height:1.7;color:#2d2d2d;">{before}</p>'
                )

            # The CTA button
            html_paragraphs.append(f'''<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:8px 0 24px 0;">
  <tr>
    <td style="border-radius:8px;background:#1a73e8;" bgcolor="#1a73e8">
      <a href="{preview_url}" target="_blank" style="display:inline-block;padding:14px 32px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;border-radius:8px;letter-spacing:0.3px;">Bekijk de preview website &rarr;</a>
    </td>
  </tr>
</table>''')

            if after:
                html_paragraphs.append(
                    f'<p style="margin:0 0 16px 0;font-size:15px;line-height:1.7;color:#2d2d2d;">{after}</p>'
                )
        else:
            lines = p.replace("\n", "<br>")
            html_paragraphs.append(
                f'<p style="margin:0 0 16px 0;font-size:15px;line-height:1.7;color:#2d2d2d;">{lines}</p>'
            )

    body_html = "\n".join(html_paragraphs)

    # Build the full HTML email
    return f'''<!DOCTYPE html>
<html lang="nl" xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>Preview website{' voor ' + business_name if business_name else ''}</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f6f9;-webkit-font-smoothing:antialiased;">

<!-- Outer wrapper -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f4f6f9;">
  <tr>
    <td align="center" style="padding:32px 16px;">

      <!-- Email card -->
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%;background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);">

        <!-- Accent bar -->
        <tr>
          <td style="height:4px;background:linear-gradient(90deg,#1a73e8,#6c5ce7);font-size:0;line-height:0;">&nbsp;</td>
        </tr>

        <!-- Header: Dan's intro -->
        <tr>
          <td style="padding:28px 36px 0 36px;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="width:44px;vertical-align:top;">
                  <!-- Avatar circle -->
                  <div style="width:40px;height:40px;border-radius:20px;background:#1a73e8;color:#ffffff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:17px;font-weight:600;line-height:40px;text-align:center;">D</div>
                </td>
                <td style="padding-left:12px;vertical-align:center;">
                  <p style="margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:15px;font-weight:600;color:#1a1a1a;">Dan van AiBoostly</p>
                  <p style="margin:2px 0 0 0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:12px;color:#888;">AI Web Specialist</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Divider -->
        <tr>
          <td style="padding:16px 36px 0 36px;">
            <div style="height:1px;background-color:#eef0f3;"></div>
          </td>
        </tr>

        <!-- Email body -->
        <tr>
          <td style="padding:24px 36px 8px 36px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
            {body_html}
          </td>
        </tr>

        <!-- Footer divider -->
        <tr>
          <td style="padding:0 36px;">
            <div style="height:1px;background-color:#eef0f3;"></div>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:20px 36px 24px 36px;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
              <tr>
                <td style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:12px;color:#aaa;line-height:1.5;">
                  <span style="font-weight:600;color:#888;">AiBoostly</span>&nbsp;&nbsp;·&nbsp;&nbsp;Arnhem, NL<br>
                  AI-websites voor lokale ondernemers
                </td>
              </tr>
            </table>
          </td>
        </tr>

      </table>
      <!-- /Email card -->

    </td>
  </tr>
</table>
<!-- /Outer wrapper -->

</body>
</html>'''
