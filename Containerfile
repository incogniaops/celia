# syntax=docker/dockerfile:1

FROM python:3.12.7-slim-bookworm AS builder

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app

# Corporate networks behind a TLS-inspecting proxy (e.g. Zscaler) need their
# root CA trusted to reach PyPI during the build. Passed as a build secret so
# it is never copied into an image layer or present in the final image — the
# final stage below only copies the already-installed package, not this cert.
# Pass with: --secret id=corp_ca_cert,src=/path/to/ca.pem
# Omit --secret entirely on networks that don't need it (e.g. the homelab).
RUN --mount=type=secret,id=corp_ca_cert \
    if [ -s /run/secrets/corp_ca_cert ]; then \
      cp /run/secrets/corp_ca_cert /usr/local/share/ca-certificates/corp-ca.crt && \
      update-ca-certificates; \
    fi && \
    pip install --no-cache-dir --target /install .

# Tectonic (data-sharing's PDF export): a single self-contained LaTeX engine
# binary, not a full TeX Live install -- see
# openspec/changes/archive/.../data-sharing-pdf-export/design.md for why.
# TARGETARCH is set automatically by buildah/buildkit; the case below maps it
# to Tectonic's musl release triples (statically linked, no glibc-version
# coupling to the final stage's base image).
ARG TARGETARCH
ARG TECTONIC_VERSION=0.17.0
RUN --mount=type=secret,id=corp_ca_cert \
    if [ -s /run/secrets/corp_ca_cert ]; then \
      cp /run/secrets/corp_ca_cert /usr/local/share/ca-certificates/corp-ca.crt && \
      update-ca-certificates; \
    fi && \
    apt-get update -qq && apt-get install -y --no-install-recommends -qq curl ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    case "$TARGETARCH" in \
      amd64) TECTONIC_TRIPLE=x86_64-unknown-linux-musl ;; \
      arm64) TECTONIC_TRIPLE=aarch64-unknown-linux-musl ;; \
      *) echo "Unsupported TARGETARCH: $TARGETARCH" >&2; exit 1 ;; \
    esac && \
    curl -sL -o /tmp/tectonic.tar.gz \
      "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40${TECTONIC_VERSION}/tectonic-${TECTONIC_VERSION}-${TECTONIC_TRIPLE}.tar.gz" && \
    tar xzf /tmp/tectonic.tar.gz -C /usr/local/bin tectonic && \
    rm /tmp/tectonic.tar.gz

# Warm Tectonic's package cache at build time (tikz, pgfplots, groupplots,
# article class -- everything the real report template uses) so generating a
# report at runtime needs no network access, which a homelab VM may not
# reliably have. Renders the REAL template (app/pdf_export/warmup.py, with
# synthetic sample data) rather than a separately hand-maintained throwaway
# document -- a stand-in document drifted from the real template twice during
# implementation (a mismatched \documentclass option, then a missing pgfplots
# library), so warming with the real template makes that drift impossible.
# See design.md's "Tectonic's package cache is warmed at image-build time"
# decision.
RUN --mount=type=secret,id=corp_ca_cert \
    if [ -s /run/secrets/corp_ca_cert ]; then \
      cp /run/secrets/corp_ca_cert /usr/local/share/ca-certificates/corp-ca.crt && \
      update-ca-certificates; \
    fi && \
    mkdir -p /tmp/warmup-out && \
    PYTHONPATH=/install python3 -m app.pdf_export.warmup > /tmp/warmup.tex && \
    HOME=/root tectonic --outdir /tmp/warmup-out /tmp/warmup.tex && \
    test -s /root/.cache/tectonic/bundles/data/*.index

FROM python:3.12.7-slim-bookworm

WORKDIR /app

RUN useradd --create-home --shell /usr/sbin/nologin celia

COPY --from=builder /install /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/tectonic /usr/local/bin/tectonic
COPY --from=builder --chown=celia:celia /root/.cache/tectonic /home/celia/.cache/tectonic
COPY app ./app

USER celia

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
