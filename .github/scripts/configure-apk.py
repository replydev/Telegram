"""Configure only the disposable CI checkout; never print credential values."""

import base64
import binascii
import os
from pathlib import Path
import re
from xml.sax.saxutils import escape


def replace_once(path, pattern, replacement):
    content, count = re.subn(pattern, replacement, path.read_text())
    if count != 1:
        raise SystemExit(f"Expected one configuration entry in {path}")
    path.write_text(content)


required = (
    "TELEGRAM_API_ID", "TELEGRAM_API_HASH", "ANDROID_KEYSTORE_BASE64",
    "ANDROID_KEYSTORE_PASSWORD", "ANDROID_KEY_ALIAS", "ANDROID_KEY_PASSWORD",
)
missing = [name for name in required if not os.environ.get(name)]
if missing:
    raise SystemExit("Missing repository secrets: " + ", ".join(missing))

api_id = os.environ["TELEGRAM_API_ID"]
api_hash = os.environ["TELEGRAM_API_HASH"]
if not re.fullmatch(r"[0-9]+", api_id) or not 0 < int(api_id) < 2**31:
    raise SystemExit("TELEGRAM_API_ID must be a positive 32-bit integer")
if not re.fullmatch(r"[0-9a-fA-F]{32}", api_hash):
    raise SystemExit("TELEGRAM_API_HASH must contain 32 hexadecimal characters")
if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+", os.environ["APP_PACKAGE"]):
    raise SystemExit("APP_PACKAGE must be a valid Android application ID")

try:
    keystore = base64.b64decode("".join(os.environ["ANDROID_KEYSTORE_BASE64"].split()), validate=True)
except binascii.Error:
    raise SystemExit("ANDROID_KEYSTORE_BASE64 is not valid base64") from None
if not keystore:
    raise SystemExit("ANDROID_KEYSTORE_BASE64 decoded to an empty file")

build_vars = Path("TMessagesProj/src/main/java/org/telegram/messenger/BuildVars.java")
replace_once(build_vars, r"public static int APP_ID = \d+;", f"public static int APP_ID = {int(api_id)};")
replace_once(build_vars, r'public static String APP_HASH = "[^"]*";', f'public static String APP_HASH = "{api_hash}";')

# Change localized names too, so the launcher name does not depend on language.
app_name = os.environ["APP_NAME"]
for path in Path("TMessagesProj/src/main/res").glob("values*/strings.xml"):
    content = path.read_text()
    for resource, name in (("AppName", app_name), ("AppNameBeta", app_name + " Beta")):
        value = escape(name.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"'))
        content = re.sub(
            rf'(<string name="{resource}">)[^<]*(</string>)',
            lambda match: match[1] + value + match[2], content,
        )
    path.write_text(content)

# Increment on each workflow run so subsequent APKs can update installed builds.
replace_once(
    Path("gradle.properties"), r"(?m)^APP_VERSION_CODE=(\d+)$",
    lambda match: f"APP_VERSION_CODE={int(match[1]) + int(os.environ['GITHUB_RUN_NUMBER'])}",
)
key_path = Path("TMessagesProj/config/release.keystore")
key_path.write_bytes(keystore)
key_path.chmod(0o600)
