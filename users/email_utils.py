"""
users/email_utils.py
=====================
Email utilities using Brevo (formerly SendinBlue) SMTP.
Free tier: 300 emails/day — perfect for university projects.

Setup:
  1. brevo.com → Sign Up (free)
  2. SMTP & API → SMTP → Generate SMTP Key
  3. Add Railway environment variables:
     EMAIL_HOST=smtp-relay.brevo.com
     EMAIL_PORT=587
     EMAIL_USE_TLS=True
     EMAIL_HOST_USER=your-brevo-email@gmail.com
     EMAIL_HOST_PASSWORD=your-brevo-smtp-key
     DEFAULT_FROM_EMAIL=UniGroups <your-brevo-email@gmail.com>
"""
from django.core.mail import send_mail
from django.conf      import settings
import logging

logger = logging.getLogger(__name__)


def send_verification_email(user, otp_code):
    """Send OTP verification email via Brevo SMTP."""

    subject = 'UniGroups — Email Verification Code'

    # Plain text fallback
    text_body = f"""
Assalam o Alaikum {user.name},

Your UniGroups verification code is:

  {otp_code}

This code expires in 10 minutes.
Your Roll Number: {user.roll_number}

If you did not register, please ignore this email.

— UniGroups | Superior University
"""

    # HTML email
    html_body = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>
  body {{ margin:0; padding:0; background:#f4f5f7; font-family:'Segoe UI',Arial,sans-serif; }}
  .wrap {{ max-width:520px; margin:40px auto; background:#fff; border-radius:16px; overflow:hidden; box-shadow:0 4px 24px rgba(0,0,0,0.08); }}
  .header {{ background:linear-gradient(135deg,#6366f1,#4f46e5); padding:32px 40px; text-align:center; }}
  .header h1 {{ color:#fff; margin:0; font-size:22px; font-weight:700; letter-spacing:-0.3px; }}
  .header p  {{ color:rgba(255,255,255,0.75); margin:6px 0 0; font-size:12px; }}
  .body {{ padding:36px 40px; }}
  .greeting {{ font-size:15px; color:#334155; margin-bottom:20px; }}
  .otp-box {{ background:#f0f4ff; border:2px solid #c7d2fe; border-radius:14px; padding:24px; text-align:center; margin:24px 0; }}
  .otp-label {{ font-size:11px; color:#6b7280; font-weight:700; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:12px; }}
  .otp-code {{ font-size:46px; font-weight:900; color:#4f46e5; letter-spacing:14px; font-family:'Courier New',monospace; line-height:1; }}
  .otp-expiry {{ font-size:11px; color:#9ca3af; margin-top:10px; }}
  .roll-box {{ background:#f8faff; border:1px solid #e0e7ff; border-radius:10px; padding:14px 18px; margin:20px 0; display:flex; align-items:center; gap:12px; }}
  .roll-icon {{ font-size:20px; }}
  .roll-label {{ font-size:10px; color:#6b7280; font-weight:700; text-transform:uppercase; letter-spacing:0.8px; }}
  .roll-number {{ font-size:16px; font-weight:800; color:#1e293b; letter-spacing:1.5px; margin-top:2px; font-family:'Courier New',monospace; }}
  .note {{ font-size:12px; color:#94a3b8; margin-top:24px; line-height:1.7; }}
  .footer {{ background:#f8faff; padding:18px 40px; text-align:center; border-top:1px solid #e2e8f0; }}
  .footer p {{ font-size:11px; color:#94a3b8; margin:0; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>UniGroups</h1>
    <p>Superior University · Group Management System</p>
  </div>
  <div class="body">
    <p class="greeting">Assalam o Alaikum <strong>{user.name}</strong>,</p>
    <p style="color:#475569;font-size:14px;margin:0 0 4px;">Enter this code to verify your email:</p>

    <div class="otp-box">
      <div class="otp-label">Verification Code</div>
      <div class="otp-code">{otp_code}</div>
      <div class="otp-expiry">⏱ Expires in 10 minutes</div>
    </div>

    <div class="roll-box">
      <div class="roll-icon">🎓</div>
      <div>
        <div class="roll-label">Your Roll Number</div>
        <div class="roll-number">{user.roll_number}</div>
      </div>
    </div>

    <p class="note">
      If you did not register on UniGroups, you can safely ignore this email.<br>
      Never share this code with anyone.
    </p>
  </div>
  <div class="footer">
    <p>Superior University · Group Management System · Powered by Brevo</p>
  </div>
</div>
</body>
</html>
"""

    try:
        send_mail(
            subject        = subject,
            message        = text_body,
            from_email     = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [user.email],
            html_message   = html_body,
            fail_silently  = False,
        )
        logger.info(f'[EMAIL] Verification sent → {user.email} ({user.roll_number})')
        return True

    except Exception as e:
        logger.error(f'[EMAIL] FAILED → {user.email}: {e}')
        return False


def send_welcome_email(user):
    """Send welcome email after successful verification."""
    try:
        html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>
  body {{ margin:0; padding:0; background:#f4f5f7; font-family:'Segoe UI',Arial,sans-serif; }}
  .wrap {{ max-width:520px; margin:40px auto; background:#fff; border-radius:16px; overflow:hidden; box-shadow:0 4px 24px rgba(0,0,0,0.08); }}
  .header {{ background:linear-gradient(135deg,#6366f1,#4f46e5); padding:32px 40px; text-align:center; }}
  .header h1 {{ color:#fff; margin:0; font-size:22px; font-weight:700; }}
  .body {{ padding:36px 40px; text-align:center; }}
  .check {{ font-size:52px; margin-bottom:12px; }}
  .title {{ font-size:22px; font-weight:800; color:#1e293b; margin-bottom:6px; }}
  .sub {{ font-size:14px; color:#64748b; margin-bottom:24px; }}
  .info {{ background:#f0fdf4; border:1px solid #bbf7d0; border-radius:12px; padding:16px 20px; text-align:left; }}
  .row {{ display:flex; justify-content:space-between; padding:5px 0; font-size:13px; }}
  .lbl {{ color:#6b7280; }}
  .val {{ font-weight:700; color:#1e293b; }}
  .dept {{ color:{'#f97316' if user.department == 'SE' else '#06b6d4'}; }}
  .footer {{ background:#f8faff; padding:18px 40px; text-align:center; border-top:1px solid #e2e8f0; }}
  .footer p {{ font-size:11px; color:#94a3b8; margin:0; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="header"><h1>UniGroups ✓</h1></div>
  <div class="body">
    <div class="check">🎉</div>
    <div class="title">Account Verified!</div>
    <div class="sub">Marhaba {user.name}, aap ka account active ho gaya!</div>
    <div class="info">
      <div class="row"><span class="lbl">Roll Number</span><span class="val" style="font-family:monospace">{user.roll_number}</span></div>
      <div class="row"><span class="lbl">Name</span><span class="val">{user.name}</span></div>
      <div class="row"><span class="lbl">Department</span><span class="val dept">{user.get_department_display() or 'Not set'}</span></div>
      <div class="row"><span class="lbl">Login with</span><span class="val">Roll Number + Password</span></div>
    </div>
  </div>
  <div class="footer"><p>Superior University · Group Management System</p></div>
</div>
</body>
</html>
"""
        send_mail(
            subject        = 'Welcome to UniGroups! 🎓',
            message        = f'Marhaba {user.name}! Your account {user.roll_number} is now verified.',
            from_email     = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [user.email],
            html_message   = html,
            fail_silently  = True,
        )
    except Exception as e:
        logger.error(f'[EMAIL] Welcome email failed → {user.email}: {e}')
