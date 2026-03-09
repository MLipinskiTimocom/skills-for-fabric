#!/usr/bin/env python3
"""
Skill Quality Checker for skills-for-fabric
Validates skill files for semantic disambiguation, structural compliance, and content quality.
"""
import re
import json
import sys
import io
import os
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
from urllib.parse import urlparse
import yaml

# Fix Unicode output on Windows (cp1252 can't handle emoji)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Optional: requests for link validation
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Optional: tiktoken for accurate token counting
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


class QualityChecker:
    # Token thresholds for recommendations
    TOKEN_THRESHOLD_WARNING = 8000    # Warn if skill exceeds this
    TOKEN_THRESHOLD_CRITICAL = 15000  # Critical if skill exceeds this
    TOKEN_THRESHOLD_TOTAL = 50000     # Warn if total exceeds this
    
    def __init__(self):
        self.results = {
            'overall_status': 'PASSED',
            'files_scanned': 0,
            'critical_count': 0,
            'warning_count': 0,
            'semantic_conflicts': [],
            'duplicate_triggers': [],
            'ambiguous_triggers': [],  # New: semantically similar triggers across skills
            'broken_references': [],
            'structural_issues': [],
            'content_warnings': [],
            'skills': {},
            'token_costs': {},        # skill_name -> {total, files: [{path, tokens}]}
            'recommendations': []     # List of actionable recommendations
        }
        self.all_skills: Dict[str, Dict] = {}  # skill_name -> {description, triggers, path}
        self._tiktoken_encoder = None
    
    def _get_encoder(self):
        """Get tiktoken encoder, lazy-loaded."""
        if self._tiktoken_encoder is None and TIKTOKEN_AVAILABLE:
            self._tiktoken_encoder = tiktoken.get_encoding('cl100k_base')
        return self._tiktoken_encoder
    
    def count_tokens(self, content: str) -> int:
        """Count tokens in content using tiktoken or fallback estimation."""
        encoder = self._get_encoder()
        if encoder:
            return len(encoder.encode(content))
        else:
            # Fallback: estimate ~4 chars per token
            return len(content) // 4
        
    def extract_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """Extract YAML frontmatter from markdown content."""
        if not content.startswith('---'):
            return {}, content
        
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}, content
        
        try:
            frontmatter = yaml.safe_load(parts[1])
            body = parts[2]
            return frontmatter if frontmatter else {}, body
        except yaml.YAMLError:
            return {}, content
    
    def extract_triggers(self, description: str) -> Set[str]:
        """Extract trigger phrases from skill description."""
        triggers = set()
        
        # Extract quoted phrases
        quoted = re.findall(r'"([^"]+)"', description)
        triggers.update(quoted)
        
        # Extract phrases after "Triggers:" 
        trigger_match = re.search(r'Triggers?:\s*(.+?)(?:\.|$)', description, re.IGNORECASE)
        if trigger_match:
            trigger_text = trigger_match.group(1)
            # Split by comma and clean up
            for phrase in trigger_text.split(','):
                phrase = phrase.strip().strip('"\'')
                if phrase and len(phrase) > 3:
                    triggers.add(phrase.lower())
        
        # Extract "when user wants to" items
        wants_match = re.search(r'when the user wants to[:\s]+(.+?)(?:Triggers|$)', description, re.IGNORECASE | re.DOTALL)
        if wants_match:
            items = re.findall(r'\((\d+)\)\s*([^(]+)', wants_match.group(1))
            for _, item in items:
                item = item.strip().rstrip(',.')
                if item and len(item) > 3:
                    triggers.add(item.lower())
        
        return triggers
    
    def calculate_similarity(self, desc1: str, desc2: str) -> float:
        """Calculate Jaccard similarity between two descriptions."""
        # Tokenize to words, lowercase
        words1 = set(re.findall(r'\b\w{3,}\b', desc1.lower()))
        words2 = set(re.findall(r'\b\w{3,}\b', desc2.lower()))
        
        # Remove common stop words
        stop_words = {'the', 'and', 'for', 'from', 'with', 'this', 'that', 'when', 'user', 'use', 'using'}
        words1 -= stop_words
        words2 -= stop_words
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def check_semantic_disambiguation(self):
        """Check for overlapping or conflicting skill descriptions."""
        skill_names = list(self.all_skills.keys())
        
        for i, skill1 in enumerate(skill_names):
            for skill2 in skill_names[i+1:]:
                if skill1 == 'check-updates' or skill2 == 'check-updates':
                    continue  # Skip utility skill
                
                desc1 = self.all_skills[skill1].get('description', '')
                desc2 = self.all_skills[skill2].get('description', '')
                
                similarity = self.calculate_similarity(desc1, desc2)
                
                if similarity >= 0.3:
                    self.results['semantic_conflicts'].append({
                        'skill1': skill1,
                        'skill2': skill2,
                        'similarity': round(similarity, 2),
                        'reason': f'{int(similarity*100)}% description overlap - may cause ambiguous skill routing'
                    })
                    self.results['critical_count'] += 1
    
    def build_similarity_matrix(self):
        """Build a Jaccard similarity matrix between all skill descriptions."""
        skill_names = [s for s in self.all_skills.keys() if s != 'check-updates']
        n = len(skill_names)
        
        if n < 2:
            return
        
        # Build matrix
        matrix = []
        for i, skill1 in enumerate(skill_names):
            row = []
            desc1 = self.all_skills[skill1].get('description', '')
            for j, skill2 in enumerate(skill_names):
                if i == j:
                    row.append(1.0)
                elif j < i:
                    # Use already computed value (symmetric)
                    row.append(matrix[j][i])
                else:
                    desc2 = self.all_skills[skill2].get('description', '')
                    similarity = self.calculate_similarity(desc1, desc2)
                    row.append(round(similarity, 2))
            matrix.append(row)
        
        self.results['similarity_matrix'] = {
            'skills': skill_names,
            'matrix': matrix
        }
    
    def check_trigger_uniqueness(self):
        """Check for duplicate trigger phrases across skills."""
        trigger_to_skills: Dict[str, Set[str]] = {}
        
        for skill_name, skill_data in self.all_skills.items():
            if skill_name == 'check-updates':
                continue
            
            for trigger in skill_data.get('triggers', set()):
                trigger_lower = trigger.lower().strip()
                if len(trigger_lower) > 5:  # Skip very short triggers
                    if trigger_lower not in trigger_to_skills:
                        trigger_to_skills[trigger_lower] = set()
                    trigger_to_skills[trigger_lower].add(skill_name)
        
        for trigger, skills in trigger_to_skills.items():
            if len(skills) > 1:
                self.results['duplicate_triggers'].append({
                    'trigger': trigger,
                    'skills': list(skills)
                })
                self.results['critical_count'] += 1
    
    def check_semantic_trigger_ambiguity(self):
        """Check for semantically similar triggers that could cause routing confusion."""
        # Common action phrases that could match multiple skills
        ambiguous_patterns = [
            ('run sql', ['run sql', 'execute sql', 'sql query', 'query']),
            ('show tables', ['show tables', 'list tables', 'show me the tables', 'what tables']),
            ('explore data', ['explore data', 'explore', 'query the data', 'query data']),
            ('describe schema', ['describe schema', 'describe', 'schema', 'describe columns']),
            ('query', ['query', 'run query', 'execute query']),
        ]
        
        # Build a map of which skills match which patterns
        pattern_matches: Dict[str, List[Tuple[str, str]]] = {}  # pattern -> [(skill, matching_trigger)]
        
        for skill_name, skill_data in self.all_skills.items():
            if skill_name == 'check-updates':
                continue
            
            desc_lower = skill_data.get('description', '').lower()
            triggers = skill_data.get('triggers', set())
            
            for pattern_name, pattern_variants in ambiguous_patterns:
                for variant in pattern_variants:
                    # Check if variant appears in description or triggers
                    found_in = None
                    if variant in desc_lower:
                        found_in = f'description contains "{variant}"'
                    else:
                        for trigger in triggers:
                            if variant in trigger.lower():
                                found_in = f'trigger "{trigger}"'
                                break
                    
                    if found_in:
                        if pattern_name not in pattern_matches:
                            pattern_matches[pattern_name] = []
                        # Avoid duplicates for same skill
                        if not any(s == skill_name for s, _ in pattern_matches[pattern_name]):
                            pattern_matches[pattern_name].append((skill_name, found_in))
                        break  # Only count once per pattern per skill
        
        # Report patterns that match multiple skills
        for pattern, matches in pattern_matches.items():
            if len(matches) > 1:
                self.results['ambiguous_triggers'].append({
                    'trigger_phrase': pattern,
                    'skills': [{'skill': s, 'match': m} for s, m in matches],
                    'ambiguity': f'Could match {len(matches)} skills'
                })
                self.results['warning_count'] += 1
    
    def check_cross_references(self, content: str, skill_path: Path, skill_name: str):
        """Check that relative paths in markdown links exist."""
        # Find markdown links: [text](path)
        links = re.findall(r'\[([^\]]*)\]\(([^)]+)\)', content)
        seen_paths = set()
        
        for text, link_path in links:
            # Skip external URLs
            if link_path.startswith('http://') or link_path.startswith('https://'):
                continue
            
            # Skip anchors
            if link_path.startswith('#'):
                continue
            
            # Remove anchor from path
            link_path_clean = link_path.split('#')[0]
            
            if not link_path_clean:
                continue
            
            # Skip duplicates within same file
            if link_path_clean in seen_paths:
                continue
            seen_paths.add(link_path_clean)
            
            # Resolve relative path
            base_dir = skill_path.parent
            resolved = (base_dir / link_path_clean).resolve()
            
            if not resolved.exists():
                self.results['broken_references'].append({
                    'skill': skill_name,
                    'path': link_path_clean,
                    'expected': str(resolved)
                })
                self.results['critical_count'] += 1
    
    def check_structural_compliance(self, content: str, frontmatter: Dict, skill_name: str) -> Dict:
        """Check structural requirements for skill files."""
        checks = {
            'has_frontmatter': bool(frontmatter),
            'has_name': 'name' in frontmatter,
            'has_description': 'description' in frontmatter,
            'has_update_notice': False,
            'has_must_prefer_avoid': False,
            'has_examples': False,
            'code_blocks_tagged': True,
            'untagged_code_blocks': 0
        }
        
        # Skip update notice check for check-updates skill
        if skill_name == 'check-updates':
            checks['has_update_notice'] = True  # N/A
        else:
            # Check for update notice blockquote
            update_patterns = [
                r'>\s*\*\*Update Check',
                r'>\s*Update Check',
                r'check-updates'
            ]
            for pattern in update_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    checks['has_update_notice'] = True
                    break
        
        # Check for Must/Prefer/Avoid sections
        mpa_patterns = [
            r'###?\s*(MUST|Must)\s*(DO)?',
            r'###?\s*(PREFER|Prefer)',
            r'###?\s*(AVOID|Avoid)',
            r'###?\s*Gotchas',
            r'###?\s*Rules'
        ]
        mpa_count = sum(1 for p in mpa_patterns if re.search(p, content))
        checks['has_must_prefer_avoid'] = mpa_count >= 2
        
        # Check for examples
        example_patterns = [
            r'###?\s*Example',
            r'```\w+\n[^`]+\n```',  # Code blocks
            r'User:\s*"',  # Prompt examples
        ]
        checks['has_examples'] = any(re.search(p, content) for p in example_patterns)
        
        # Check code block language tags (only opening fences, not closing)
        # Match ``` at start of line, optionally followed by language, then newline
        # Exclude closing fences by requiring they not be preceded by content on same line
        code_blocks = re.findall(r'^```(\w*)\s*$', content, re.MULTILINE)
        # Filter: only count as untagged if it's an opening fence (odd positions are opens, even are closes)
        # Actually simpler: opening fences can have language, closing never do
        # Count pairs - every 2nd match is a closing fence
        opening_fences = code_blocks[::2]  # Every other match starting from 0
        untagged = sum(1 for lang in opening_fences if not lang)
        checks['untagged_code_blocks'] = untagged
        checks['code_blocks_tagged'] = untagged == 0
        
        # Report issues
        if not checks['has_frontmatter']:
            self.results['structural_issues'].append({
                'skill': skill_name,
                'severity': 'CRITICAL',
                'message': 'Missing YAML frontmatter'
            })
            self.results['critical_count'] += 1
        
        if checks['has_frontmatter'] and not checks['has_name']:
            self.results['structural_issues'].append({
                'skill': skill_name,
                'severity': 'CRITICAL', 
                'message': 'Missing "name" field in frontmatter'
            })
            self.results['critical_count'] += 1
        
        if checks['has_frontmatter'] and not checks['has_description']:
            self.results['structural_issues'].append({
                'skill': skill_name,
                'severity': 'CRITICAL',
                'message': 'Missing "description" field in frontmatter'
            })
            self.results['critical_count'] += 1
        
        if not checks['has_update_notice'] and skill_name != 'check-updates':
            self.results['structural_issues'].append({
                'skill': skill_name,
                'severity': 'CRITICAL',
                'message': 'Missing update check notice blockquote'
            })
            self.results['critical_count'] += 1
        
        if not checks['has_must_prefer_avoid']:
            self.results['structural_issues'].append({
                'skill': skill_name,
                'severity': 'WARNING',
                'message': 'Missing Must/Prefer/Avoid or Gotchas/Rules sections'
            })
            self.results['warning_count'] += 1
        
        if not checks['has_examples']:
            self.results['structural_issues'].append({
                'skill': skill_name,
                'severity': 'WARNING',
                'message': 'Missing examples section or code examples'
            })
            self.results['warning_count'] += 1
        
        if untagged > 0:
            self.results['content_warnings'].append({
                'skill': skill_name,
                'message': f'{untagged} code block(s) missing language tag'
            })
            self.results['warning_count'] += 1
        
        return checks
    
    def check_description_length(self, description: str, skill_name: str):
        """Check description length limits."""
        desc_len = len(description)
        
        # Critical: description exceeds 1023 characters (blocks check-in)
        if desc_len > 1023:
            self.results['structural_issues'].append({
                'skill': skill_name,
                'severity': 'CRITICAL',
                'message': f'Description exceeds 1023 characters ({desc_len} chars) - must shorten to allow check-in'
            })
            self.results['critical_count'] += 1
        # Warning: description approaching limit (>= 900 characters)
        elif desc_len >= 900:
            self.results['content_warnings'].append({
                'skill': skill_name,
                'message': f'Description approaching limit ({desc_len}/1023 chars) - consider shortening'
            })
            self.results['warning_count'] += 1
    
    def check_description_quality(self, description: str, skill_name: str):
        """Check description quality for discoverability."""
        issues = []
        
        # Check mentions specific technologies
        tech_keywords = ['sql', 't-sql', 'python', 'powershell', 'bash', 'cli', 
                        'rest', 'api', 'sdk', 'fabric', 'warehouse', 'lakehouse',
                        'spark', 'notebook', 'pipeline', 'dataflow']
        desc_lower = description.lower()
        has_tech = any(tech in desc_lower for tech in tech_keywords)
        if not has_tech:
            issues.append('Description should mention specific technologies')
        
        # Check has trigger phrases
        if 'trigger' not in desc_lower and 'when' not in desc_lower and 'use' not in desc_lower:
            issues.append('Description should include trigger phrases or usage context')
        
        for issue in issues:
            self.results['content_warnings'].append({
                'skill': skill_name,
                'message': issue
            })
            self.results['warning_count'] += 1
    
    def check_naming_convention(self, skill_name: str):
        """Check skill naming follows conventions."""
        if skill_name == 'check-updates':
            return  # Utility skill, skip
        
        valid_patterns = [
            r'^[a-z]+-authoring-[a-z]+$',   # Developer skills
            r'^[a-z]+-consumption-[a-z]+$', # Consumer skills  
            r'^e2e-[a-z-]+$',               # Cross-artifact skills
            r'^[a-z-]+$'                    # General pattern (flexible)
        ]
        
        # Check for recommended patterns
        recommended = [
            r'^[a-z]+-authoring-[a-z]+$',
            r'^[a-z]+-consumption-[a-z]+$',
            r'^e2e-[a-z-]+$'
        ]
        
        matches_recommended = any(re.match(p, skill_name) for p in recommended)
        
        if not matches_recommended:
            self.results['content_warnings'].append({
                'skill': skill_name,
                'message': f'Consider naming pattern: {{endpoint}}-authoring-{{access}} or {{endpoint}}-consumption-{{access}}'
            })
            self.results['warning_count'] += 1
    
    def check_external_links(self, content: str, skill_name: str):
        """Validate external URLs are accessible (rate-limited)."""
        if not REQUESTS_AVAILABLE:
            return
        
        # Find external URLs
        urls = re.findall(r'https?://[^\s\)>\]]+', content)
        
        # Sample max 5 links to avoid slowdown
        urls = list(set(urls))[:5]
        
        for url in urls:
            # Skip GitHub raw content (often requires auth)
            if 'raw.githubusercontent.com' in url:
                continue
            
            try:
                response = requests.head(url, timeout=5, allow_redirects=True)
                if response.status_code >= 400:
                    self.results['content_warnings'].append({
                        'skill': skill_name,
                        'message': f'Link may be broken (HTTP {response.status_code}): {url[:60]}...'
                    })
                    self.results['warning_count'] += 1
            except requests.RequestException:
                # Network issues, skip silently
                pass
    
    def check_content_quality(self, content: str, skill_name: str):
        """Check content quality metrics."""
        # Use accurate token counting
        estimated_tokens = self.count_tokens(content)
        
        # Flag very large files
        if estimated_tokens > 10000:
            self.results['content_warnings'].append({
                'skill': skill_name,
                'message': f'Large file (~{estimated_tokens} tokens) - consider splitting into focused skills'
            })
            self.results['warning_count'] += 1
    
    def scan_skill(self, skill_path: Path) -> Dict[str, Any]:
        """Scan a single skill file."""
        skill_name = skill_path.parent.name
        
        try:
            with open(skill_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {'error': f'Could not read file: {e}'}
        
        frontmatter, body = self.extract_frontmatter(content)
        
        # Store skill metadata for cross-skill checks
        description = frontmatter.get('description', '')
        if isinstance(description, str):
            description = description.strip()
        else:
            description = str(description) if description else ''
        
        self.all_skills[skill_name] = {
            'description': description,
            'triggers': self.extract_triggers(description),
            'path': str(skill_path)
        }
        
        # Run structural checks
        checks = self.check_structural_compliance(content, frontmatter, skill_name)
        
        # Run cross-reference checks
        self.check_cross_references(content, skill_path, skill_name)
        
        # Run description quality checks
        if description:
            self.check_description_length(description, skill_name)
            self.check_description_quality(description, skill_name)
        
        # Run naming convention checks
        self.check_naming_convention(skill_name)
        
        # Run content quality checks
        self.check_content_quality(content, skill_name)
        
        # Run external link validation (rate-limited)
        self.check_external_links(content, skill_name)
        
        # Calculate token costs for all files in skill
        self.calculate_token_costs(skill_path, skill_name)
        
        return checks
    
    def calculate_token_costs(self, skill_path: Path, skill_name: str):
        """Calculate token costs for all files in a skill directory."""
        skill_dir = skill_path.parent
        total_tokens = 0
        file_costs = []
        try:
            with open(skill_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            tokens = self.count_tokens(content)
            total_tokens += tokens
            rel_path = str(skill_path.relative_to(skill_dir))
            file_costs.append({'path': rel_path, 'tokens': tokens})
        except Exception:
            pass
        
        # Sort by tokens descending
        file_costs.sort(key=lambda x: -x['tokens'])
        
        self.results['token_costs'][skill_name] = {
            'total': total_tokens,
            'files': file_costs
        }
        
        return total_tokens
    
    def generate_recommendations(self):
        """Generate actionable recommendations based on all checks."""
        recommendations = []
        
        # Token cost recommendations
        total_tokens = sum(tc['total'] for tc in self.results['token_costs'].values())
        
        for skill_name, token_data in self.results['token_costs'].items():
            skill_tokens = token_data['total']
            
            if skill_tokens > self.TOKEN_THRESHOLD_CRITICAL:
                recommendations.append({
                    'severity': 'CRITICAL',
                    'skill': skill_name,
                    'category': 'token_cost',
                    'message': f'Skill uses {skill_tokens:,} tokens (>{self.TOKEN_THRESHOLD_CRITICAL:,}) - strongly consider splitting into smaller skills or using resource routing',
                    'impact': 'High token costs increase latency and API costs'
                })
            elif skill_tokens > self.TOKEN_THRESHOLD_WARNING:
                recommendations.append({
                    'severity': 'WARNING',
                    'skill': skill_name,
                    'category': 'token_cost',
                    'message': f'Skill uses {skill_tokens:,} tokens (>{self.TOKEN_THRESHOLD_WARNING:,}) - consider splitting or trimming',
                    'impact': 'Moderate token costs may impact performance'
                })
        
        if total_tokens > self.TOKEN_THRESHOLD_TOTAL:
            recommendations.append({
                'severity': 'WARNING',
                'skill': None,
                'category': 'token_cost',
                'message': f'Total token cost across all skills is {total_tokens:,} (>{self.TOKEN_THRESHOLD_TOTAL:,})',
                'impact': 'High aggregate costs if multiple skills are loaded'
            })
        
        # Ambiguous trigger recommendations
        for amb in self.results['ambiguous_triggers']:
            skills_list = ', '.join([s['skill'] for s in amb['skills']])
            recommendations.append({
                'severity': 'WARNING',
                'skill': None,
                'category': 'disambiguation',
                'message': f'Trigger "{amb["trigger_phrase"]}" matches multiple skills: {skills_list}',
                'impact': 'May cause incorrect skill routing'
            })
        
        # Description length recommendations
        for issue in self.results['structural_issues']:
            if 'description' in issue.get('message', '').lower() and 'exceeds' in issue.get('message', '').lower():
                recommendations.append({
                    'severity': 'CRITICAL',
                    'skill': issue['skill'],
                    'category': 'description',
                    'message': issue['message'],
                    'impact': 'Blocks plugin check-in'
                })
        
        # Similarity recommendations
        for conflict in self.results['semantic_conflicts']:
            recommendations.append({
                'severity': 'CRITICAL',
                'skill': f"{conflict['skill1']} & {conflict['skill2']}",
                'category': 'similarity',
                'message': f"{conflict['similarity']*100:.0f}% description similarity - differentiate these skills",
                'impact': 'High similarity causes ambiguous routing'
            })
        
        self.results['recommendations'] = recommendations
        return recommendations
    
    def scan_repository(self) -> bool:
        """Scan all skill files in the repository."""
        print("🔍 skills-for-fabric QUALITY CHECK")
        print("=" * 50)
        
        # Find skill files (only in skills/, exclude graveyard)
        skill_files = []
        for skill_md in Path('skills').glob('**/SKILL.md'):
            # Skip graveyard
            if 'graveyard' in str(skill_md):
                continue
            skill_files.append(skill_md)
        
        if not skill_files:
            print("⚠️  No skill files found to scan")
            return True
        
        # First pass: scan all skills
        for skill_path in skill_files:
            skill_name = skill_path.parent.name
            print(f"\n📄 Scanning: {skill_name}")
            
            checks = self.scan_skill(skill_path)
            self.results['files_scanned'] += 1
            
            if 'error' in checks:
                print(f"   ❌ Error: {checks['error']}")
                continue
            
            self.results['skills'][skill_name] = checks
        
        # Second pass: cross-skill checks
        print("\n🔀 Running cross-skill analysis...")
        self.check_semantic_disambiguation()
        self.check_trigger_uniqueness()
        self.check_semantic_trigger_ambiguity()
        self.build_similarity_matrix()
        
        # Determine overall status
        if self.results['critical_count'] > 0:
            self.results['overall_status'] = 'CRITICAL'
        elif self.results['warning_count'] > 0:
            self.results['overall_status'] = 'WARNING'
        else:
            self.results['overall_status'] = 'PASSED'
        
        # Print summary
        print(f"\n{'='*50}")
        print("📊 QUALITY CHECK SUMMARY")
        print(f"Files scanned: {self.results['files_scanned']}")
        print(f"Critical issues: {self.results['critical_count']}")
        print(f"Warnings: {self.results['warning_count']}")
        
        if self.results['semantic_conflicts']:
            print(f"\n🔀 Semantic conflicts: {len(self.results['semantic_conflicts'])}")
            for conflict in self.results['semantic_conflicts']:
                print(f"   - {conflict['skill1']} <-> {conflict['skill2']}: {conflict['reason']}")
        
        if self.results['duplicate_triggers']:
            print(f"\n🎯 Duplicate triggers: {len(self.results['duplicate_triggers'])}")
            for dup in self.results['duplicate_triggers']:
                print(f"   - \"{dup['trigger']}\" used by: {', '.join(dup['skills'])}")
        
        if self.results['ambiguous_triggers']:
            print(f"\n⚠️  Semantically ambiguous triggers: {len(self.results['ambiguous_triggers'])}")
            print(f"\n   | {'Trigger Phrase':<20} | {'Matches These Skills':<50} | Ambiguity |")
            print(f"   |{'-'*22}|{'-'*52}|{'-'*11}|")
            for amb in self.results['ambiguous_triggers']:
                skills_str = ', '.join([s['skill'] for s in amb['skills']])
                print(f"   | {amb['trigger_phrase']:<20} | {skills_str:<50} | {len(amb['skills'])} skills |")
        
        # Print similarity matrix
        if 'similarity_matrix' in self.results and self.results['similarity_matrix']:
            matrix_data = self.results['similarity_matrix']
            skills = matrix_data['skills']
            matrix = matrix_data['matrix']
            
            print(f"\n📊 Skill Similarity Matrix (Jaccard)")
            
            # Calculate column width based on skill names
            max_name_len = max(len(s) for s in skills)
            col_width = max(6, min(max_name_len, 12))
            
            # Header row with abbreviated skill names
            abbrevs = [s[:col_width] for s in skills]
            header = "   " + " " * (max_name_len + 2) + " | ".join(f"{a:>{col_width}}" for a in abbrevs)
            print(header)
            print("   " + "-" * len(header))
            
            # Data rows
            for i, skill in enumerate(skills):
                row_values = []
                for j, val in enumerate(matrix[i]):
                    if i == j:
                        row_values.append(f"{'---':^{col_width}}")
                    elif val >= 0.3:
                        row_values.append(f"{val:>{col_width}.0%}🚨")
                    elif val >= 0.2:
                        row_values.append(f"{val:>{col_width}.0%}⚠️")
                    else:
                        row_values.append(f"{val:>{col_width}.0%}")
                row_str = " | ".join(row_values)
                print(f"   {skill:<{max_name_len}} | {row_str}")
            
            print(f"\n   Legend: 🚨 >=30% (critical), ⚠️ 20-30% (review), values show Jaccard similarity")
        
        if self.results['broken_references']:
            print(f"\n🔗 Broken references: {len(self.results['broken_references'])}")
            for ref in self.results['broken_references']:
                print(f"   - {ref['skill']}: {ref['path']}")
        
        # Print token costs
        if self.results['token_costs']:
            print(f"\n💰 TOKEN COSTS")
            print(f"   {'Skill':<30} {'Tokens':>12} {'Files':>8}")
            print(f"   {'-'*30} {'-'*12} {'-'*8}")
            
            # Sort by tokens descending
            sorted_costs = sorted(
                self.results['token_costs'].items(),
                key=lambda x: -x[1]['total']
            )
            
            total_tokens = 0
            for skill_name, token_data in sorted_costs:
                tokens = token_data['total']
                files = len(token_data['files'])
                total_tokens += tokens
                
                # Add warning indicator
                indicator = ""
                if tokens > self.TOKEN_THRESHOLD_CRITICAL:
                    indicator = " 🚨"
                elif tokens > self.TOKEN_THRESHOLD_WARNING:
                    indicator = " ⚠️"
                
                print(f"   {skill_name:<30} {tokens:>12,} {files:>8}{indicator}")
            
            print(f"   {'-'*30} {'-'*12} {'-'*8}")
            total_indicator = " ⚠️" if total_tokens > self.TOKEN_THRESHOLD_TOTAL else ""
            print(f"   {'TOTAL':<30} {total_tokens:>12,}{total_indicator}")
            
            # Print detailed breakdown for large skills
            large_skills = [(s, d) for s, d in sorted_costs if d['total'] > self.TOKEN_THRESHOLD_WARNING]
            if large_skills:
                print(f"\n   Detailed breakdown (skills > {self.TOKEN_THRESHOLD_WARNING:,} tokens):")
                for skill_name, token_data in large_skills:
                    print(f"\n   {skill_name} ({token_data['total']:,} tokens):")
                    for f in token_data['files'][:5]:  # Top 5 files
                        pct = (f['tokens'] / token_data['total'] * 100) if token_data['total'] > 0 else 0
                        print(f"      {f['path']:<40} {f['tokens']:>8,} ({pct:>5.1f}%)")
        
        # Generate and print recommendations
        self.generate_recommendations()
        
        if self.results['recommendations']:
            print(f"\n📋 RECOMMENDATIONS ({len(self.results['recommendations'])})")
            
            # Group by severity
            critical_recs = [r for r in self.results['recommendations'] if r['severity'] == 'CRITICAL']
            warning_recs = [r for r in self.results['recommendations'] if r['severity'] == 'WARNING']
            
            if critical_recs:
                print(f"\n   🚨 Critical ({len(critical_recs)}):")
                for rec in critical_recs:
                    skill_str = f"[{rec['skill']}] " if rec['skill'] else ""
                    print(f"      {skill_str}{rec['message']}")
            
            if warning_recs:
                print(f"\n   ⚠️  Warnings ({len(warning_recs)}):")
                for rec in warning_recs:
                    skill_str = f"[{rec['skill']}] " if rec['skill'] else ""
                    print(f"      {skill_str}{rec['message']}")
        
        if self.results['overall_status'] == 'CRITICAL':
            print(f"\n❌ RESULT: FAILED - {self.results['critical_count']} critical issue(s)")
            return False
        elif self.results['overall_status'] == 'WARNING':
            print(f"\n⚠️  RESULT: PASSED with {self.results['warning_count']} warning(s)")
            return True
        else:
            print(f"\n✅ RESULT: PASSED - All quality checks passed!")
            return True
    
    def save_report(self, output_file: str = 'quality-report.json'):
        """Save quality report to JSON file."""
        # Convert sets to lists for JSON serialization
        for skill_name, skill_data in self.all_skills.items():
            if 'triggers' in skill_data and isinstance(skill_data['triggers'], set):
                skill_data['triggers'] = list(skill_data['triggers'])
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Report saved to: {output_file}")


def main():
    """Main entry point for CI/CD pipeline."""
    checker = QualityChecker()
    
    try:
        passed = checker.scan_repository()
        checker.save_report()
        
        if checker.results['overall_status'] == 'CRITICAL':
            print("\n❌ CRITICAL ISSUES FOUND - BUILD FAILED")
            sys.exit(1)
        else:
            print("\n✅ QUALITY CHECK COMPLETE")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n💥 QUALITY CHECK FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
