FROM python:3.10-slim

# نصب پیش‌نیازها
RUN apt-get update && apt-get install -y --no-install-recommends \
    certbot \
    && rm -rf /var/lib/apt/lists/*

# نصب کتابخانه‌های پایتون
RUN pip install --no-cache-dir requests

# کپی اسکریپت پایتون
COPY manage_certs.py /usr/local/bin/manage_certs.py
RUN chmod +x /usr/local/bin/manage_certs.py

# ایجاد پوشه haproxy برای گواهینامه‌ها
RUN mkdir -p /etc/letsencrypt/haproxy

# تنظیمات محیطی
ENV CONFIG_DIR=/etc/haproxy/cfg \
    CERT_DIR=/etc/letsencrypt \
    CHECK_INTERVAL=43200

# اجرای وب‌سرور و اسکریپت
CMD ["/bin/sh", "-c", "python3 -m http.server 80 --directory /etc/letsencrypt/webroot & python3 /usr/local/bin/manage_certs.py"]