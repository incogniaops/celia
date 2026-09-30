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

FROM python:3.12.7-slim-bookworm

WORKDIR /app

COPY --from=builder /install /usr/local/lib/python3.12/site-packages
COPY app ./app

RUN useradd --create-home --shell /usr/sbin/nologin celia
USER celia

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
