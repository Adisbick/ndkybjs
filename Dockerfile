FROM alpine:3.20

ARG SING_BOX_VERSION=1.13.11
ARG TARGETARCH

RUN apk add --no-cache ca-certificates curl tar bash jq python3 py3-pip tzdata openssl \
  && case "${TARGETARCH:-amd64}" in \
      amd64) SB_ARCH="amd64" ;; \
      arm64) SB_ARCH="arm64" ;; \
      *) echo "Unsupported arch: ${TARGETARCH}" && exit 1 ;; \
    esac \
  && curl -fsSL -o /tmp/sing-box.tar.gz \
      "https://github.com/SagerNet/sing-box/releases/download/v${SING_BOX_VERSION}/sing-box-${SING_BOX_VERSION}-linux-${SB_ARCH}.tar.gz" \
  && tar -xzf /tmp/sing-box.tar.gz -C /tmp \
  && install -m 0755 /tmp/sing-box-${SING_BOX_VERSION}-linux-${SB_ARCH}/sing-box /usr/local/bin/sing-box \
  && rm -rf /tmp/sing-box*

WORKDIR /app
COPY entrypoint.sh /app/entrypoint.sh
COPY sub_server.py /app/sub_server.py
RUN chmod +x /app/entrypoint.sh

ENV DATA_DIR=/data \
    CONFIG_FILE=/data/config.json \
    SUB_PORT=8080 \
    SNI=adm.com \
    VLESS_TCP_PORT=443 \
    VLESS_HU_PORT=8443 \
    ANYTLS_PORT=9443 \
    VLESS_HU_PATH=/up \
    NODE_NAME=private-node \
    BLOCK_PRIVATE=true \
    BLOCK_BITTORRENT=true

EXPOSE 443/tcp 8443/tcp 9443/tcp 8080/tcp

ENTRYPOINT ["/app/entrypoint.sh"]
