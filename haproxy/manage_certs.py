import os
import re
import subprocess
import time
import logging
from pathlib import Path
import shutil

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths and settings
CONFIG_DIR = os.getenv('CONFIG_DIR', '/etc/haproxy/cfg')
CERT_DIR = os.getenv('CERT_DIR', '/etc/letsencrypt')
WEBROOT_DIR = os.path.join(CERT_DIR, 'webroot')
HAPROXY_CERT_DIR = os.path.join(CERT_DIR, 'haproxy')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 43200))  # 12 ساعت

# Regex pattern to extract domains
DOMAIN_PATTERN = re.compile(r'hdr\(host\)\s+-i\s+(\S+)', re.IGNORECASE)

def ensure_webroot():
    """Ensure webroot directory exists"""
    webroot_path = Path(WEBROOT_DIR)
    try:
        webroot_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Webroot directory ensured at {WEBROOT_DIR}")
    except Exception as e:
        logger.error(f"Failed to create webroot directory {WEBROOT_DIR}: {e}")
        raise

def ensure_haproxy_cert_dir():
    """Ensure HAProxy cert directory exists"""
    haproxy_cert_path = Path(HAPROXY_CERT_DIR)
    try:
        haproxy_cert_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Haproxy cert directory ensured at {HAPROXY_CERT_DIR}")
    except Exception as e:
        logger.error(f"Failed to create haproxy cert directory {HAPROXY_CERT_DIR}: {e}")
        raise

def generate_dummy_certificate():
    """Generate a self-signed dummy certificate in HAPROXY_CERT_DIR"""
    try:
        ensure_haproxy_cert_dir()
        
        dst_fullchain = Path(HAPROXY_CERT_DIR) / "dummy.pem"
        dst_privkey = Path(HAPROXY_CERT_DIR) / "dummy.pem.key"
        
        if not dst_fullchain.exists():
            cmd = [
                'openssl', 'req', '-x509', '-nodes', '-days', '365', '-newkey', 'rsa:2048',
                '-keyout', str(dst_privkey),
                '-out', str(dst_fullchain),
                '-subj', '/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=localhost'
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            os.chmod(dst_fullchain, 0o644)
            os.chmod(dst_privkey, 0o644)
            logger.info(f"Generated dummy certificate at {dst_fullchain} and key at {dst_privkey}")
        else:
            logger.info(f"Dummy certificate already exists at {dst_fullchain}")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to generate dummy certificate: {e.stderr}")
    except Exception as e:
        logger.error(f"Failed to generate dummy certificate: {e}")

def copy_certificates_to_haproxy(domain):
    """Combine fullchain and privkey into a single PEM file for HAProxy"""
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
            os.chmod(dst_fullchain, 0o644)
            logger.info(f"Copied fullchain.pem to {dst_fullchain}")
        else:
            logger.error(f"Source fullchain.pem not found for {domain}")
            return
            
        if src_privkey.exists():
            shutil.copy(src_privkey, dst_privkey)
            os.chmod(dst_privkey, 0o644)
            logger.info(f"Copied privkey.pem to {dst_privkey}")
        else:
            logger.error(f"Source privkey.pem not found for {domain}")
            return
            
    except Exception as e:
        logger.error(f"Failed to copy certificates for {domain}: {e}")

def get_domains_from_configs():
    """Extract domains from .cfg files"""
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
    """Obtain or renew certificate for a domain"""
    cert_path = Path(CERT_DIR) / 'live' / domain / 'fullchain.pem'
    
    # Check if certificate exists
    if cert_path.exists():
        logger.info(f"Certificate for {domain} already exists")
        copy_certificates_to_haproxy(domain)  # Copy existing certificates
        return
    
    # Ensure webroot exists
    ensure_webroot()
    
    # Run Certbot to obtain certificate without email
    cmd = [
        'certbot', 'certonly', '--non-interactive', '--agree-tos',
        '--register-unsafely-without-email',
        '--webroot', '-w', WEBROOT_DIR, '-d', domain
    ]
    
    try:
        logger.info(f"Requesting certificate for {domain}")
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Certificate for {domain} obtained successfully")
        copy_certificates_to_haproxy(domain)   # Copy existing certificates
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to obtain certificate for {domain}: {e.stderr}")

def renew_certificates():
    """Renew certificates nearing expiration"""
    try:
        logger.info("Checking for certificate renewals")
        subprocess.run(['certbot', 'renew', '--non-interactive', '--webroot', '-w', WEBROOT_DIR], check=True, capture_output=True, text=True)
        logger.info("Certificate renewal check completed")
        
        # Combine renewed certificates for all domains
        domains = get_domains_from_configs()
        for domain in domains:
            cert_path = Path(CERT_DIR) / 'live' / domain / 'fullchain.pem'
            if cert_path.exists():
                copy_certificates_to_haproxy(domain)
                
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to renew certificates: {e.stderr}")

def main():
    """Main loop to check files and certificates"""
    # Generate dummy certificate on startup
    generate_dummy_certificate()
    
    while True:
        try:
            # Extract domains
            domains = get_domains_from_configs()
            
            # Obtain certificates for new domains
            for domain in domains:
                ensure_certificate(domain)
            
            # Check for certificate renewals
            renew_certificates()
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        
        # Wait until next check
        logger.info(f"Sleeping for {CHECK_INTERVAL} seconds")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()