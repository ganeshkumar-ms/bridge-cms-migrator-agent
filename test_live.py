import json
import urllib.request
import urllib.error

API_BASE = "https://hjwkic438k.execute-api.us-east-1.amazonaws.com"
CLOUDFRONT_URL = "https://d23utb1q5zn42x.cloudfront.net"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.getcode(), resp.read().decode('utf-8')

def post_json(url, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.getcode(), json.loads(resp.read().decode('utf-8'))

def test_live():
    print("=== LIVE AWS VERIFICATION FOR BRIDGE ===")
    
    # 1. Health check
    print(f"\n1. Testing GET {API_BASE}/api/health ...")
    try:
        code, text = get(f"{API_BASE}/api/health")
        print(f"   Status: {code}, Response: {text}")
        assert code == 200
        print("   -> PASS: Health check OK")
    except Exception as e:
        print(f"   -> FAIL: Health check error: {e}")
        return False

    # 2. "bro" test
    print(f"\n2. Testing POST {API_BASE}/api/bridge/migrate with text 'bro' ...")
    try:
        code, data = post_json(f"{API_BASE}/api/bridge/migrate", {
            "content": "bro"
        })
        print(f"   Status: {code}")
        print(f"   Data type: {data.get('type')}, message: {data.get('message')}")
        assert data.get("type") == "chat"
        assert "bro" in data.get("message", "").lower() or "bridge" in data.get("message", "").lower()
        print("   -> PASS: 'bro' smooth chat response verified!")
    except Exception as e:
        print(f"   -> FAIL: 'bro' test error: {e}")
        return False

    # 3. Conversational query test
    print(f"\n3. Testing POST {API_BASE}/api/bridge/migrate with 'yo bro what can you do' ...")
    try:
        code, data = post_json(f"{API_BASE}/api/bridge/migrate", {
            "content": "yo bro what can you do"
        })
        print(f"   Status: {code}")
        print(f"   Data type: {data.get('type')}, message snippet: {data.get('message', '')[:100]}...")
        assert data.get("type") == "chat"
        assert len(data.get("message", "")) > 10
        print("   -> PASS: Conversational inquiry response verified!")
    except Exception as e:
        print(f"   -> FAIL: Conversational query error: {e}")
        return False

    # 4. CMS migration transformation test
    print(f"\n4. Testing POST {API_BASE}/api/bridge/migrate with WordPress content ...")
    wp_sample = """
    post_title: BFSI Quarterly Wealth Portfolio Update
    post_date: 2026-11-10
    post_author: Priya Sharma
    post_content: <!-- wp:paragraph --><p>Our wealth division posted a 14.2% YoY gain in AUM for Q3 2026.</p><!-- /wp:paragraph -->
    post_status: publish
    custom_fields:
      client_tier: Ultra HNI
      tax_bracket: 30%
    """
    try:
        code, data = post_json(f"{API_BASE}/api/bridge/migrate", {
            "content": wp_sample,
            "source_cms": "wordpress",
            "target_cms": "contentful"
        })
        print(f"   Status: {code}")
        mr = data.get("migration_readiness", {})
        print(f"   Migration Score: {mr.get('score')}")
        print(f"   Status: {mr.get('status')}")
        print(f"   Mapped Fields: {len(data.get('field_mappings', []))}")
        assert mr.get('score', 0) > 0
        assert len(data.get('field_mappings', [])) > 0
        print("   -> PASS: CMS Schema Migration test OK")
    except Exception as e:
        print(f"   -> FAIL: CMS Schema Migration error: {e}")
        return False

    # 5. CloudFront Web UI distribution check
    print(f"\n5. Testing GET {CLOUDFRONT_URL} ...")
    try:
        code, text = get(CLOUDFRONT_URL)
        print(f"   Status: {code}, Length: {len(text)} bytes")
        assert code == 200
        print("   -> PASS: CloudFront Web UI distribution live and serving HTML OK")
    except Exception as e:
        print(f"   -> FAIL: CloudFront check error: {e}")
        return False

    print("\n==========================================")
    print(" ALL LIVE TESTS PASSED 100% FOR BRIDGE!")
    print("==========================================")
    return True

if __name__ == "__main__":
    test_live()
