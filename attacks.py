"""The 16 reportable attack types, mapped to the five incident categories evaluated in the study.
(code, platform name used in the text, covered by the evaluated guidance?)"""
ATTACKS = {
    "Phishing email": ("ph", "", 1), "Fake website": ("ph", "", 1),
    "Gmail account hacked": ("hk", "Gmail", 1), "Instagram account hacked": ("hk", "Instagram", 1),
    "Facebook account hacked": ("hk", "Facebook", 1), "WhatsApp account hijacked": ("hk", "WhatsApp", 1),
    "Malware": ("rw", "", 1), "Virus": ("rw", "", 1), "Ransomware": ("rw", "", 1),
    "Identity theft": ("id", "", 1), "UPI fraud": ("upi", "", 1),
    "Credit card fraud": ("upi", "", 0), "OTP scam": ("upi", "", 0),
    "Data breach": ("hk", "", 0), "Password leak": ("hk", "", 0), "Wi-Fi attack": ("rw", "", 0),
}

TIPS = {
    "Passwords": ["Use a long, unique password for every account; a password manager makes this practical.",
                  "Never share passwords, OTPs or your UPI PIN with anyone, including someone who says they are from your bank.",
                  "Turn on two-factor login with an authenticator app wherever it is offered."],
    "Safe browsing": ["Type your bank’s address yourself or use its official app instead of following links in messages.",
                      "Check for a misspelt address before you enter any password or card details.",
                      "Install apps only from the official app store, and be wary of apps that ask to share your screen."],
    "Email security": ["Treat urgent messages about blocked accounts, refunds or prizes as suspicious until you verify them another way.",
                       "Don’t open unexpected attachments, even from known contacts, without confirming with them.",
                       "Report phishing to your email provider so it can be blocked for others."],
    "Social media": ["Turn on two-factor login and review which devices and apps are connected to your account.",
                     "If a friend suddenly asks for money, call them to confirm before sending anything.",
                     "Keep your recovery email and phone number current and secured."],
    "Banking and UPI": ["You never enter your UPI PIN to receive money. A collect request means you will pay.",
                        "Report an unauthorised transaction to your bank as soon as you see it; the zero-liability window is 3 working days.",
                        "Call 1930 for financial cyber fraud and file at cybercrime.gov.in."],
    "Backups and devices": ["Keep a recent backup offline or on a service the device can’t overwrite.",
                            "Install system updates promptly and use a reputable security app.",
                            "Use a strong Wi-Fi password and avoid banking on public networks."],
}
FINAL_CHECK = ["I changed the passwords of every affected or linked account.",
               "Two-factor login is on for my email and banking.",
               "I checked my bank and card statements for transactions I don’t recognise.",
               "I have the complaint reference numbers from my bank and the cyber-crime portal."]
