import boto3
import json
import os
import re
import random
from pathlib import Path
from services import guardrail_service

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / '.env')
    load_dotenv()
except ImportError:
    pass


def get_bedrock_client():
    return boto3.client(
        'bedrock-runtime',
        region_name=os.getenv('AWS_DEFAULT_REGION') or os.getenv('AWS_REGION') or 'us-east-1',
    )


MODEL_ID = 'us.amazon.nova-pro-v1:0'
FALLBACK_MODEL_ID = 'us.anthropic.claude-3-haiku-20240307-v1:0'

BRIDGE_SYSTEM_PROMPT = """You are BRIDGE, an Enterprise AI CMS Migrator & Schema Transformation Engine.

You operate dynamically in TWO MODES based on user input:

==================================================
MODE 1: CONVERSATIONAL & MULTILINGUAL ASSISTANCE (type: "chat")
==================================================
Trigger this mode whenever:
- The user sends greetings, casual slang (e.g. "bro", "dude", "bhai", "machan", "yaar", "buddy", "man"), checks in, asks how you are doing, or chats conversationally.
- The user speaks in ANY language (English, Tamil, Hindi, Telugu, Spanish, French, German, Arabic, etc.) conversationally or asks a general question.
- The user asks about your capabilities, architecture, supported CMS platforms, or asks for advice.
- The user provides short casual remarks or feedback without an attached file or actual structured schema/content to migrate.

RULE FOR MODE 1:
- Respond smoothly, politely, naturally, and warmly in the user's language and tone.
- Answer whatever they ask directly and smoothly.
- Output ONLY this JSON format:
{
  "type": "chat",
  "message": "<Your smooth, natural conversational reply in the user's language>"
}

==================================================
MODE 2: CMS MIGRATION & SCHEMA TRANSFORMATION (type: "migration")
==================================================
Trigger this mode whenever:
- The user has attached/uploaded a file (any file: JSON, CSV, XML, SQL, Markdown, Word, PDF, HTML, text, etc.).
- The user provides an actual content draft, blog post, article, database export, schema definition, or explicitly asks to migrate/transform content into a target headless CMS schema.

=== CORE MIGRATION DELIVERABLES FOR MODE 2 ===
1. SCHEMA MAPPING MATRIX:
   - For every detected or inferred field, define:
     * source_field (e.g., 'post_title', 'field_lead_paragraph', 'body')
     * target_field (e.g., 'title', 'excerpt', 'bodyRichText', 'slug')
     * source_type (e.g., 'varchar(255)', 'longtext/html', 'datetime')
     * target_type (e.g., 'Symbol (Short text)', 'RichText AST', 'ISO 8601 Date')
     * transform_rule (e.g., 'Direct Map', 'HTML to RichText AST', 'Date Normalize to UTC', 'Slugify & Lowercase', 'Taxonomy Lookup')
     * status: 'DIRECT_MAP' | 'TRANSFORM' | 'EXCEPTION' | 'OPTIONAL'
     * sample_value: representative string showing source -> target transformation
     * notes: actionable guidance on character limits, unique indexes, or nested components.

2. MIGRATION READINESS & RISK SCORE:
   - Calculate an objective 0–100 score:
     * 85–100: "READY_TO_MIGRATE" (clean field alignment, standard types)
     * 50–84: "TRANSFORMS_REQUIRED" (HTML cleanup, date parsing, or taxonomy remapping needed)
     * 0–49: "SCHEMA_CONFLICTS" (missing mandatory target fields, incompatible data types, unresolvable relations)

3. FIELD EXCEPTIONS & RISKS:
   - Identify missing required fields (e.g., target requires 'slug' but legacy only has numeric ID).
   - Flag unhosted asset paths (e.g., local '/wp-content/uploads/...' needing DAM ingestion).
   - Warn on character overflows or unmapped relational IDs.
   - For every exception:
     * Severity: 'CRITICAL' | 'WARNING' | 'SUGGESTION'
     * Field name, Issue description, Risk to data integrity, Suggested migration action

4. READY-TO-USE TARGET PAYLOAD:
   - Generate a valid, clean sample JSON payload conforming to modern headless standards.

OUTPUT FORMAT FOR MODE 2:
{
  "type": "migration",
  "migration_readiness": {
    "status": "READY_TO_MIGRATE" | "TRANSFORMS_REQUIRED" | "SCHEMA_CONFLICTS",
    "score": 85,
    "summary": "Executive migration assessment in 2 sentences."
  },
  "metrics": {
    "mapped_fields_count": 5,
    "transforms_needed_count": 2,
    "exceptions_count": 1,
    "source_system": "Legacy CMS / Source Content",
    "target_system": "Headless CMS (Contentful/Strapi)"
  },
  "field_mappings": [ ... ],
  "exceptions": [ ... ],
  "target_payload": { ... },
  "checklist": [ ... ]
}
"""

GREETING_RESPONSES = [
    "Hello! I am BRIDGE, your Enterprise CMS Migrator & Schema Transformation Engine. Share any legacy CMS export, schema definition, JSON, CSV, or document draft, and I will analyze source-to-target field mapping, flag exceptions, and generate a migration-ready payload.",
    "Hi there! Welcome to BRIDGE. I help you migrate content between CMS platforms (WordPress, Drupal, Contentful, Strapi, Sanity, AEM) with zero data loss. Paste your schema or attach a content file to begin.",
    "Greetings! I am BRIDGE. Ready to inspect your content architecture. Share any database export, blog draft, or content payload, and I will build a field mapping matrix with transform rules.",
    "Hello! Ready when you are. Upload a document or schema, and I'll evaluate migration readiness, detect missing mandatory fields, and output the transformed target payload.",
    "Hey there! Welcome to BRIDGE. Feel free to paste or attach any content you want migrated. I'll analyze schema compatibility with zero hallucinations."
]

BRO_RESPONSES = [
    "Hey bro! Ready when you are. Share any file, content export, schema, or document draft, and I'll map and transform it cleanly for your target CMS.",
    "Yo bro! What's up? I'm BRIDGE, your CMS Migrator & Schema Engine. Drop any file or paste what you need to move, and we'll get it migrated with zero data loss.",
    "Hey bro! All systems operational. Send over any file or paste your content/schema, and I'll generate the field mapping matrix and target payload for you.",
    "Sup bro! Ready to roll. You can upload any file (JSON, CSV, Word, PDF, SQL, etc.) or chat about your CMS architecture anytime."
]

HOW_ARE_YOU_RESPONSES = [
    "I'm operating at peak performance and ready to map your CMS schemas! Paste any legacy content, schema definitions, or upload an export file to analyze migration paths.",
    "All schema transformation pipelines, field mappers, and AST converters are standing by! How can I assist your content migration today?",
    "Doing very well, thank you! I'm ready to transform your next legacy content set into modern headless CMS schemas.",
    "I'm ready to assist! Share your source schema or content export, and I'll check for type mismatches, missing mandatory fields, and migration readiness."
]


def _pick_varied_response(pool: list, conversation_history: list) -> str:
    used = set()
    for m in (conversation_history or []):
        c = m.get('content', '')
        if isinstance(c, dict):
            c = c.get('message', '')
        if isinstance(c, str):
            used.add(c.strip())
    fresh = [r for r in pool if r.strip() not in used]
    return random.choice(fresh if fresh else pool)


def _match_quick_conversational(user_text: str, conversation_history: list):
    cleaned = re.sub(r'[^\w\s]', '', (user_text or '').strip().lower())
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    if not cleaned:
        return None

    # Casual brother/slang words (bro, bruh, dude, yaar, bhai, machan, etc.)
    is_bro = (
        bool(re.match(r'^(?:(?:hey+|hi+|yo+|sup|hello+|namaste|vanakkam)\s+)?(?:bro+|brother|bruh|brah|dude|yaar|bhai|bhaiya|machan|macha|thala|buddy|mate|man|sis|dost)(?:\s+(?:how\s+are\s+you|whats?\s+up|hw\s+r\s+u))?$', cleaned)) or
        cleaned in {'bro', 'broo', 'bruh', 'brah', 'brother', 'dude', 'yaar', 'bhai', 'machan', 'macha', 'thala', 'buddy', 'mate', 'sis', 'dost'}
    )
    if is_bro:
        return _pick_varied_response(BRO_RESPONSES, conversation_history)

    # "How are you" variants and typos
    is_how_are_you = (
        bool(re.match(r'^(?:(?:hi+|h[ea]y+|h[ea]llo+|hlo|ji)\s+)?(?:how|hw)\s+(?:r|are|re)\s+(?:u|you|yu)(?:\s+doing)?$', cleaned)) or
        bool(re.match(r'^(?:hows?|hws)\s+(?:it\s+going|u|you)$', cleaned)) or
        cleaned in {'hru', 'hw r u', 'how r u', 'how r you', 'how are you', 'how are u', 'whats up', 'sup', 'how do you do'}
    )
    if is_how_are_you:
        return _pick_varied_response(HOW_ARE_YOU_RESPONSES, conversation_history)

    # Greeting variants including typos (ji, gi, helo, hlo, etc.)
    is_greeting = (
        bool(re.match(r'^(?:hi+|h[ea]y+|h[ea]llo+|hlo|helo|ji+|namaste|hola|greetings?|yo+|sup)(?:\s+(?:there|bridge|agent|bot|all|team|friend|buddy|ji))?$', cleaned)) or
        bool(re.match(r'^(?:good\s+(?:morning|afternoon|evening|day))(?:\s+(?:bridge|there|all))?$', cleaned)) or
        cleaned in {'ji', 'hi', 'hello', 'hey', 'hii', 'hiii', 'heyy', 'namaste ji', 'gi', 'hlo', 'helo', 'hlw', 'hye', 'hay'}
    )
    if is_greeting:
        return _pick_varied_response(GREETING_RESPONSES, conversation_history)

    return None


def _rule_based_migration_fallback(content: str, file_name: str = "") -> dict:
    # If this was short conversational text without a file or schema markers, reply as chat
    clean_strip = (content or '').strip()
    is_short = len(clean_strip) < 65 and not file_name
    schema_signals = ['post_', 'table', 'schema', 'wp_', '{', '[', 'select', 'create table', 'http', 'class ', 'def ', 'migration']
    has_schema_signals = any(sig in clean_strip.lower() for sig in schema_signals)

    if is_short and not has_schema_signals:
        return {
            "type": "chat",
            "message": "Hello! I am BRIDGE. I'm ready to assist you. Share any content draft, database export, schema file, or document, and I'll map and transform it smoothly into your target CMS."
        }

    title = file_name.replace('_', ' ').replace('-', ' ').title() if file_name else "Source Content Set"
    slug = re.sub(r'[^a-z0-9]+', '-', (file_name or "content-item").lower()).strip('-')

    has_html = bool(re.search(r'<[a-z][\s\S]*>', content, re.IGNORECASE))
    has_date = bool(re.search(r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b', content))

    mappings = [
        {
            "source_field": "title / heading",
            "target_field": "title",
            "source_type": "string",
            "target_type": "Symbol (Short text)",
            "transform_rule": "Direct Map",
            "status": "DIRECT_MAP",
            "sample_value": title,
            "notes": "Direct transfer, within standard 256 character title limit."
        },
        {
            "source_field": "filename / identifier",
            "target_field": "slug",
            "source_type": "string",
            "target_type": "Symbol (Unique Slug)",
            "transform_rule": "Slugify & Lowercase",
            "status": "DIRECT_MAP",
            "sample_value": slug,
            "notes": "Enforce lowercase alphanumeric and unique index in target CMS."
        },
        {
            "source_field": "body / document_text",
            "target_field": "bodyRichText",
            "source_type": "html_string" if has_html else "text_string",
            "target_type": "RichText AST",
            "transform_rule": "HTML to RichText AST" if has_html else "Markdown to AST Blocks",
            "status": "TRANSFORM",
            "sample_value": content[:120].strip() + "...",
            "notes": "Strip inline font-size and color tags; convert structural headings to H2/H3 nodes."
        }
    ]

    exceptions = []
    if has_html and re.search(r'<img\s+[^>]*src=[\'"]([^\'"]+)[\'"]', content, re.IGNORECASE):
        exceptions.append({
            "id": "EXC-1",
            "severity": "WARNING",
            "field": "embedded_images",
            "issue": "Content embeds inline <img> tags referencing legacy paths.",
            "risk": "Target headless CMS requires asset references in media library rather than hardcoded URLs.",
            "suggested_action": "Extract image sources, upload to target CMS Asset DAM, and embed as linked asset blocks."
        })

    if not has_date:
        exceptions.append({
            "id": f"EXC-{len(exceptions)+1}",
            "severity": "SUGGESTION",
            "field": "publishDate",
            "issue": "Source content lacks an explicit ISO publication timestamp.",
            "risk": "Target CMS ordering and sorting queries may fail or default to migration date.",
            "suggested_action": "Provide publication timestamp or set migration ingestion timestamp as fallback."
        })

    score = 88 if not exceptions else (65 if any(e['severity'] == 'CRITICAL' for e in exceptions) else 78)
    status = "READY_TO_MIGRATE" if score >= 85 else ("SCHEMA_CONFLICTS" if score < 50 else "TRANSFORMS_REQUIRED")

    return {
        "type": "migration",
        "migration_readiness": {
            "status": status,
            "score": score,
            "summary": f"BRIDGE mapped 3 core fields across '{title}'. {'Identified inline assets and date parameters needing conversion.' if exceptions else 'All field types and schema definitions are directly compatible.'}"
        },
        "metrics": {
            "mapped_fields_count": len(mappings),
            "transforms_needed_count": sum(1 for m in mappings if m['status'] == 'TRANSFORM'),
            "exceptions_count": len(exceptions),
            "source_system": "Legacy CMS / Document Content",
            "target_system": "Headless CMS (Contentful/Strapi)"
        },
        "field_mappings": mappings,
        "exceptions": exceptions,
        "target_payload": {
            "title": title,
            "slug": slug,
            "status": "draft",
            "excerpt": content[:140].strip() + ("..." if len(content) > 140 else "")
        },
        "checklist": [
            "Verify target CMS content type exists with matching field IDs.",
            "Run asset extraction script for embedded media references."
        ]
    }


def migrate_content(
    content: str,
    file_name: str = "",
    file_type: str = "",
    conversation_history: list = None,
    source_cms: str = "auto",
    target_cms: str = "contentful"
) -> dict:
    conversation_history = conversation_history or []

    # 1. Guardrail check
    guard_res = guardrail_service.inspect_and_sanitize(content or file_name, is_document=bool(file_name))
    if guard_res.get('blocked'):
        return {
            "type": "chat",
            "message": guard_res.get('message', 'Content blocked by enterprise security guardrails.'),
            "guardrails": guard_res.get('guardrails'),
            "rejected": True,
        }

    # 2. Rapid typo / conversational check (instant response, zero Bedrock call)
    quick = _match_quick_conversational(content, conversation_history)
    if quick:
        return {
            "type": "chat",
            "message": quick
        }

    # 3. Bedrock Nova Pro Converse invocation
    try:
        client = get_bedrock_client()

        # Build clean role-alternating history starting with user
        bedrock_messages = []
        for turn in conversation_history[-8:]:
            role = turn.get('role', 'user')
            raw_c = turn.get('content', '')
            if isinstance(raw_c, dict):
                raw_c = raw_c.get('summary', '') or raw_c.get('message', '') or json.dumps(raw_c)
            clean_c = str(raw_c or '').strip()
            if not clean_c:
                continue

            b_role = 'user' if role == 'user' else 'assistant'
            if not bedrock_messages:
                if b_role != 'user':
                    continue
                bedrock_messages.append({'role': 'user', 'content': [{'text': clean_c}]})
            else:
                if bedrock_messages[-1]['role'] == b_role:
                    bedrock_messages[-1]['content'][0]['text'] += f"\n\n{clean_c}"
                else:
                    bedrock_messages.append({'role': b_role, 'content': [{'text': clean_c}]})

        # Format user prompt distinguishing file submission from conversational text
        if file_name:
            prompt_text = f"USER SUBMITTED FILE FOR MIGRATION (Filename: {file_name}):\n\n{content}\n\nPerform full MODE 2 migration analysis."
        else:
            prompt_text = f"USER MESSAGE:\n{content}\n\nDetermine whether this is conversational/question/multilingual (MODE 1: type 'chat') OR actual content/schema to migrate (MODE 2: type 'migration'). Return appropriate JSON only."

        if not bedrock_messages or bedrock_messages[-1]['role'] != 'user':
            bedrock_messages.append({'role': 'user', 'content': [{'text': prompt_text}]})
        else:
            bedrock_messages[-1]['content'][0]['text'] += f"\n\n{prompt_text}"

        response = client.converse(
            modelId=MODEL_ID,
            messages=bedrock_messages,
            system=[{'text': BRIDGE_SYSTEM_PROMPT}],
            inferenceConfig={
                'temperature': 0.2,
                'maxTokens': 4096,
                'topP': 0.9
            }
        )

        output_text = response['output']['message']['content'][0]['text'].strip()

        # Clean markdown code blocks if wrapped
        if output_text.startswith('```'):
            output_text = re.sub(r'^```(?:json)?\s*', '', output_text)
            output_text = re.sub(r'\s*```$', '', output_text)

        parsed = json.loads(output_text)
        return parsed

    except Exception as e:
        print(f"Bedrock invocation exception, using fallback: {e}")
        return _rule_based_migration_fallback(content, file_name)


process_migration = migrate_content
