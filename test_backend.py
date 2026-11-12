import sys
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BACKEND_DIR = Path(__file__).resolve().parent / 'backend'
sys.path.insert(0, str(BACKEND_DIR))

from services import bridge_service

print("1. Testing Typo Interceptor 'ji'...")
res_ji = bridge_service.migrate_content("ji")
assert res_ji.get("type") == "chat", f"Expected chat type, got {res_ji}"
print(f"   [PASS] Responded: {res_ji.get('message')[:50]}...")

print("\n2. Testing Typo Greeting 'helo'...")
res_helo = bridge_service.migrate_content("helo")
assert res_helo.get("type") == "chat", f"Expected chat type, got {res_helo}"
print(f"   [PASS] Responded: {res_helo.get('message')[:50]}...")

print("\n3. Testing Content Migration on Sample WordPress Post...")
sample_post = """
post_title: Annual Shareholder Letter 2026
post_name: annual-shareholder-letter-2026
post_date: 2026-10-15 14:30:00
post_content: <p>We are pleased to present our record annual operational results.</p><img src="/wp-content/uploads/chart.png" alt="Revenue Chart" />
"""
res_mig = bridge_service.migrate_content(sample_post, file_name="wp_export.json")
assert "migration_readiness" in res_mig, f"Expected migration_readiness in {res_mig}"
print(f"   [PASS] Status: {res_mig['migration_readiness']['status']} (Score: {res_mig['migration_readiness']['score']})")
print(f"   [PASS] Summary: {res_mig['migration_readiness']['summary']}")
print(f"   [PASS] Mapped Fields: {len(res_mig.get('field_mappings', []))}")
print(f"   [PASS] Target Payload: {res_mig.get('target_payload')}")

print("\n==========================================")
print(" ALL BRIDGE BACKEND TESTS PASSED CLEANLY!")
print("==========================================")

