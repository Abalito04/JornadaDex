from html import escape


def build_action_email(title, message, action_label, action_url, expiry_message, closing_message):
    safe_title = escape(title)
    safe_message = escape(message)
    safe_action_label = escape(action_label)
    safe_action_url = escape(action_url, quote=True)
    safe_expiry_message = escape(expiry_message)
    safe_closing_message = escape(closing_message)

    return f"""<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{safe_title}</title>
  </head>
  <body style="margin:0;padding:0;background-color:#d4e6c7;color:#17342a;font-family:Arial,Helvetica,sans-serif;">
    <div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;">
      {safe_message}
    </div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#d4e6c7;">
      <tr>
        <td align="center" style="padding:40px 16px;">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:600px;background-color:#f0e7d3;border:1px solid #bdd8b8;border-radius:8px;overflow:hidden;">
            <tr>
              <td style="background-color:#0b7a53;padding:24px 32px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                  <tr>
                    <td align="center" width="42" height="42" style="width:42px;height:42px;border-radius:50%;background-color:#f0e7d3;color:#0b7a53;font-size:16px;font-weight:700;">JD</td>
                    <td style="padding-left:12px;color:#ffffff;font-size:21px;font-weight:700;">JornadaDex</td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:38px 32px 18px;">
                <p style="margin:0 0 12px;color:#4c6259;font-size:14px;font-weight:700;text-transform:uppercase;">Seguridad de la cuenta</p>
                <h1 style="margin:0 0 18px;color:#17342a;font-size:28px;line-height:1.25;">{safe_title}</h1>
                <p style="margin:0 0 26px;color:#17342a;font-size:16px;line-height:1.65;">{safe_message}</p>
                <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                  <tr>
                    <td align="center" style="border-radius:6px;background-color:#0b7a53;">
                      <a href="{safe_action_url}" style="display:inline-block;padding:14px 24px;color:#ffffff;font-size:16px;font-weight:700;text-decoration:none;border-radius:6px;">{safe_action_label}</a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:8px 32px 32px;">
                <div style="margin:0 0 22px;padding:16px;background-color:#e6dcc5;border-left:4px solid #0b7a53;border-radius:4px;">
                  <p style="margin:0;color:#4c6259;font-size:14px;line-height:1.55;">{safe_expiry_message}</p>
                </div>
                <p style="margin:0 0 8px;color:#4c6259;font-size:13px;line-height:1.5;">Si el boton no funciona, copia y pega este enlace en tu navegador:</p>
                <p style="margin:0;padding:12px;background-color:#eadfc8;border-radius:4px;color:#075f41;font-size:12px;line-height:1.5;word-break:break-all;">{safe_action_url}</p>
              </td>
            </tr>
            <tr>
              <td style="padding:22px 32px;background-color:#e6dcc5;border-top:1px solid #bdd8b8;">
                <p style="margin:0 0 6px;color:#17342a;font-size:13px;line-height:1.5;">{safe_closing_message}</p>
                <p style="margin:0;color:#71877d;font-size:12px;">JornadaDex &middot; AQR Estudio Contable</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""
