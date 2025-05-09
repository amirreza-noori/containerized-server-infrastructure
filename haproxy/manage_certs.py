import os
import re
import subprocess
import time
import logging
from pathlib import Path
import shutil

# تنظیمات لاگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# مسیرها و تنظیمات
CONFIG_DIR = os.getenv('CONFIG_DIR', '/etc/haproxy/cfg')
CERT_DIR = os.getenv('CERT_DIR', '/etc/letsencrypt')
WEBROOT_DIR = os.path.join(CERT_DIR, 'webroot')
HAPROXY_CERT_DIR = os.path.join(CERT_DIR, 'haproxy')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 43200))  # 12 ساعت

# الگوی regex برای استخراج دامنه‌ها
DOMAIN_PATTERN = re.compile(r'hdr\(host\)\s+-i\s+(\S+)', re.IGNORECASE)

def ensure_webroot():
    """ایجاد پوشه webroot در صورت عدم وجود"""
    webroot_path = Path(WEBROOT_DIR)
    try:
        webroot_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Webroot directory ensured at {WEBROOT_DIR}")
    except Exception as e:
        logger.error(f"Failed to create webroot directory {WEBROOT_DIR}: {e}")
        raise

def ensure_haproxy_cert_dir():
    """ایجاد پوشه haproxy در صورت عدم وجود"""
    haproxy_cert_path = Path(HAPROXY_CERT_DIR)
    try:
        haproxy_cert_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Haproxy cert directory ensured at {HAPROXY_CERT_DIR}")
    except Exception as e:
        logger.error(f"Failed to create haproxy cert directory {HAPROXY_CERT_DIR}: {e}")
        raise

def copy_certificates_to_haproxy(domain):
    """کپی و تغییر نام فایل‌های گواهینامه به پوشه haproxy"""
    try:
        ensure_haproxy_cert_dir()
        
        # مسیر فایل‌های گواهینامه
        src_fullchain = Path(CERT_DIR) / 'live' / domain / 'fullchain.pem'
        src_privkey = Path(CERT_DIR) / 'live' / domain / 'privkey.pem'
        dst_fullchain = Path(HAPROXY_CERT_DIR) / f"{domain}.pem"
        dst_privkey = Path(HAPROXY_CERT_DIR) / f"{domain}.pem.key"
        
        # کپی فایل‌ها
        if src_fullchain.exists():
            shutil.copy(src_fullchain, dst_fullchain)
            logger.info(f"Copied fullchain.pem to {dst_fullchain}")
        else:
            logger.error(f"Source fullchain.pem not found for {domain}")
            return
            
        if src_privkey.exists():
            shutil.copy(src_privkey, dst_privkey)
            logger.info(f"Copied privkey.pem to {dst_privkey}")
        else:
            logger.error(f"Source privkey.pem not found for {domain}")
            return
            
    except Exception as e:
        logger.error(f"Failed to copy certificates for {domain}: {e}")

def get_domains_from_configs():
    """استخراج دامنه‌ها از فایل‌های .cfg"""
    domains = set()
    config_path = Path(CONFIG_DIR)
    
    if not config_path.exists():
        logger.error(f"Directory {CONFIG_DIR} does not exist")
        return domains
        
    for cfg_file in config_path.glob('*.cfg'):
        try:
            with cfg_file.open('r') as f:
                content = f.read()
                matches = DOMAIN_PATTERN.findall(content)
                domains.update(matches)
                logger.info(f"Found domains in {cfg_file}: {matches}")
        except Exception as e:
            logger.error(f"Error reading {cfg_file}: {e}")
            
    return domains

def ensure_certificate(domain):
    """دریافت یا تمدید گواهینامه برای دامنه"""
    cert_path = Path(CERT_DIR) / 'live' / domain / 'fullchain.pem'
    
    # بررسی وجود گواهینامه
    if cert_path.exists():
        logger.info(f"Certificate for {domain} already exists")
        copy_certificates_to_haproxy(domain)  # کپی گواهینامه‌های موجود
        return
    
    # اطمینان از وجود پوشه webroot
    ensure_webroot()
    
    # اجرای certbot برای دریافت گواهینامه بدون ایمیل
    cmd = [
        'certbot', 'certonly', '--non-interactive', '--agree-tos',
        '--register-unsafely-without-email',
        '--webroot', '-w', WEBROOT_DIR, '-d', domain
    ]
    
    try:
        logger.info(f"Requesting certificate for {domain}")
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Certificate for {domain} obtained successfully")
        copy_certificates_to_haproxy(domain)  # کپی گواهینامه‌های جدید
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to obtain certificate for {domain}: {e.stderr}")

def renew_certificates():
    """تمدید گواهینامه‌های در حال انقضا"""
    try:
        logger.info("Checking for certificate renewals")
        subprocess.run(['certbot', 'renew', '--non-interactive', '--webroot', '-w', WEBROOT_DIR], check=True, capture_output=True, text=True)
        logger.info("Certificate renewal check completed")
        
        # کپی گواهینامه‌های تمدیدشده برای همه دامنه‌ها
        domains = get_domains_from_configs()
        for domain in domains:
            cert_path = Path(CERT_DIR) / 'live' / domain / 'fullchain.pem'
            if cert_path.exists():
                copy_certificates_to_haproxy(domain)
                
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to renew certificates: {e.stderr}")

def main():
    """حلقه اصلی برای بررسی فایل‌ها و گواهینامه‌ها"""
    while True:
        try:
            # استخراج دامنه‌ها
            domains = get_domains_from_configs()
            
            # دریافت گواهینامه برای دام  دامنه‌های جدید
            for domain in domains:
                ensure_certificate(domain)
            
            # بررسی تمدید گواهینامه‌ها
            renew_certificates()
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        
        # انتظار تا بررسی بعدی
        logger.info(f"Sleeping for {CHECK_INTERVAL} seconds")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()