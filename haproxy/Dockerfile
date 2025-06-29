FROM python:3.10-slim

# Install prerequisites
RUN apt-get update && apt-get install -y --no-install-recommends \
    certbot \
    && rm -rf /var/lib/apt/lists/*

# Install Python libraries
RUN pip install --no-cache-dir requests

# Create directories for HAProxy certificates and webroot
RUN mkdir -p /etc/letsencrypt/haproxy /etc/letsencrypt/webroot

# Copy Python script
COPY manage_certs.py /usr/local/bin/manage_certs.py
RUN chmod +x /usr/local/bin/manage_certs.py

# Environment variables
ENV CONFIG_DIR=/etc/haproxy/cfg \
    CERT_DIR=/etc/letsencrypt \
    CHECK_INTERVAL=43200

# Run Certbot
CMD ["/bin/sh", "-c", "python3 -m http.server 80 --directory /etc/letsencrypt/webroot & python3 /usr/local/bin/manage_certs.py"]