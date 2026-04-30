#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${DATA_DIR:-/data}"
CONFIG_FILE="${CONFIG_FILE:-$DATA_DIR/config.json}"
IDENTITY_FILE="$DATA_DIR/identity.env"

mkdir -p "$DATA_DIR"

# Load persisted/generated identity if present.
if [ -f "$IDENTITY_FILE" ]; then
  # shellcheck disable=SC1090
  source "$IDENTITY_FILE"
fi

UUID="${UUID:-}"
REALITY_PRIVATE_KEY="${REALITY_PRIVATE_KEY:-}"
REALITY_PUBLIC_KEY="${REALITY_PUBLIC_KEY:-}"
SHORT_ID="${SHORT_ID:-}"
ANYTLS_PASSWORD="${ANYTLS_PASSWORD:-}"

if [ -z "$UUID" ]; then
  UUID="$(python3 - <<'PY'
import uuid
print(uuid.uuid4())
PY
)"
fi

if [ -z "$REALITY_PRIVATE_KEY" ] || [ -z "$REALITY_PUBLIC_KEY" ]; then
  keypair="$(sing-box generate reality-keypair)"
  REALITY_PRIVATE_KEY="$(printf '%s\n' "$keypair" | awk -F': ' '/PrivateKey/ {print $2}')"
  REALITY_PUBLIC_KEY="$(printf '%s\n' "$keypair" | awk -F': ' '/PublicKey/ {print $2}')"
fi

if [ -z "$SHORT_ID" ]; then
  SHORT_ID="$(openssl rand -hex 8)"
fi

if [ -z "$ANYTLS_PASSWORD" ]; then
  ANYTLS_PASSWORD="$(openssl rand -base64 16)"
fi

cat > "$IDENTITY_FILE" <<EOF
UUID='$UUID'
REALITY_PRIVATE_KEY='$REALITY_PRIVATE_KEY'
REALITY_PUBLIC_KEY='$REALITY_PUBLIC_KEY'
SHORT_ID='$SHORT_ID'
ANYTLS_PASSWORD='$ANYTLS_PASSWORD'
EOF
chmod 600 "$IDENTITY_FILE"

export UUID REALITY_PRIVATE_KEY REALITY_PUBLIC_KEY SHORT_ID ANYTLS_PASSWORD

python3 /app/sub_server.py --write-config "$CONFIG_FILE"

echo "Generated sing-box config: $CONFIG_FILE"
sing-box check -c "$CONFIG_FILE"

echo "Identity summary:"
echo "  UUID=$UUID"
echo "  REALITY_PUBLIC_KEY=$REALITY_PUBLIC_KEY"
echo "  SHORT_ID=$SHORT_ID"
echo "  ANYTLS_PASSWORD=$ANYTLS_PASSWORD"
echo "  SNI=${SNI:-adm.com}"
echo "Set these values as environment variables for stable redeploys."

python3 /app/sub_server.py --serve &
exec sing-box run -c "$CONFIG_FILE"
