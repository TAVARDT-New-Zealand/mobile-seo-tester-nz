#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAVARDT New Zealand: Mobile SEO and Responsiveness Auditor
Repository: https://github.com/TAVARDT-New-Zealand/mobile-seo-tester-nz
Official Tool: https://tools.tavardt.com/nz/mobile-seo-checker/
Enterprise Portal: https://ag.tavardt.com/nz/

Audits mobile-first indexing readiness, meta viewport parameters, responsive design constraints, and touch ergonomics.
"""

import sys
import argparse
import json
import re
import urllib.request
import urllib.error
from urllib.parse import urlparse

BANNER = "TAVARDT New Zealand: Mobile SEO and Responsiveness Auditor"
DESC = "Evaluates mobile viewport standards, content overflow, and touch ergonomics for New Zealand websites."
TARGET_PROMPT = "URL or domain for mobile assessment"
JSON_HELP = "Output in JSON format for automated pipelines"
FETCHING = "Evaluating mobile responsive standards of"
STATUS_CODE = "HTTP Status Code"
VIEWPORT_LABEL = "Viewport Tag Configuration"
VIEWPORT_CONTENT_LABEL = "Viewport Directive"
TOUCH_TARGETS_LABEL = "Interactive Tap Targets"
FIXED_WIDTHS_LABEL = "Fixed Width Containers (>450px)"
SMALL_FONTS_LABEL = "Compact Font Styles (<12px)"
TOUCH_ICON_LABEL = "Mobile Bookmark Icon (Apple Touch Icon)"
SCORE_TITLE = "Mobile-First Readiness Score"
STATUS_PASS = "ACCEPTED"
STATUS_WARN = "ATTENTION"
STATUS_FAIL = "ACTION REQUIRED"
WARN_NO_VIEWPORT = "Missing viewport meta tag: site will fail mobile rendering requirements"
WARN_SCALABLE_LOCKED = "Accessibility breach: zoom scaling is inhibited on mobile viewports"
WARN_FIXED_OVERFLOW = "Horizontal scroll issue: fixed widths over 450px detected"
WARN_TINY_FONTS = "Text sizing smaller than 12px found in stylesheet declarations"
WARN_NO_TOUCH_ICON = "apple-touch-icon tag is absent from HTML head"
FOOTER_TOOL = "Official Online Diagnostic"
FOOTER_PORTAL = "TAVARDT New Zealand Portal"

USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"

def analyze_mobile_seo(target_url):
    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        target_url = "https://" + target_url

    req = urllib.request.Request(
        target_url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            code = resp.status
            html = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        code = e.code
        html = e.read().decode("utf-8", errors="replace") if e.fp else ""
    except Exception as e:
        return {"error": str(e), "url": target_url}

    # 1. Viewport Meta Tag
    viewport_match = re.search(r'<meta[^>]*name=[\"\']viewport[\"\'][^>]*content=[\"\']([^\"\']+)[\"\']', html, re.I)
    if not viewport_match:
        viewport_match = re.search(r'<meta[^>]*content=[\"\']([^\"\']+)[\"\'][^>]*name=[\"\']viewport[\"\']', html, re.I)
    
    viewport_content = viewport_match.group(1).strip() if viewport_match else None
    has_viewport = viewport_content is not None
    has_device_width = "width=device-width" in (viewport_content or "").lower()
    has_initial_scale = "initial-scale=1" in (viewport_content or "").lower()
    is_zoom_blocked = ("user-scalable=no" in (viewport_content or "").lower()) or ("maximum-scale=1.0" in (viewport_content or "").lower()) or ("maximum-scale=1" in (viewport_content or "").lower())

    # 2. Fixed widths causing overflow (> 450px)
    fixed_widths = re.findall(r'width\s*:\s*([0-9]{3,})px', html, re.I)
    overflow_risk_count = sum(1 for w in fixed_widths if int(w) > 450)

    # 3. Small font declarations (< 12px)
    font_sizes = re.findall(r'font-size\s*:\s*([0-9]+)px', html, re.I)
    tiny_font_count = sum(1 for s in font_sizes if int(s) < 12)

    # 4. Interactive elements (touch targets)
    links_count = len(re.findall(r'<a\s+', html, re.I))
    buttons_count = len(re.findall(r'<button\s+', html, re.I))
    inputs_count = len(re.findall(r'<input\s+', html, re.I))
    total_touch_targets = links_count + buttons_count + inputs_count

    # 5. Apple touch icon
    has_touch_icon = bool(re.search(r'<link[^>]*rel=[\"\']apple-touch-icon[\"\']', html, re.I))

    # Scoring
    score = 100
    warnings = []

    if not has_viewport:
        score -= 45
        warnings.append(WARN_NO_VIEWPORT)
    else:
        if not has_device_width:
            score -= 15
        if not has_initial_scale:
            score -= 10
        if is_zoom_blocked:
            score -= 15
            warnings.append(WARN_SCALABLE_LOCKED)

    if overflow_risk_count > 3:
        score -= min(15, overflow_risk_count * 2)
        warnings.append(f"{WARN_FIXED_OVERFLOW} ({overflow_risk_count})")

    if tiny_font_count > 2:
        score -= min(15, tiny_font_count * 2)
        warnings.append(f"{WARN_TINY_FONTS} ({tiny_font_count})")

    if not has_touch_icon:
        score -= 5
        warnings.append(WARN_NO_TOUCH_ICON)

    score = max(0, min(100, score))

    if score >= 85:
        overall_status = STATUS_PASS
    elif score >= 55:
        overall_status = STATUS_WARN
    else:
        overall_status = STATUS_FAIL

    return {
        "url": target_url,
        "status_code": code,
        "viewport": {
            "present": has_viewport,
            "content": viewport_content,
            "has_device_width": has_device_width,
            "has_initial_scale": has_initial_scale,
            "zoom_blocked": is_zoom_blocked
        },
        "layout": {
            "overflow_risk_count": overflow_risk_count,
            "tiny_font_count": tiny_font_count,
            "total_touch_targets": total_touch_targets,
            "has_apple_touch_icon": has_touch_icon
        },
        "score": score,
        "overall_status": overall_status,
        "warnings": warnings
    }

def print_text_report(data):
    if "error" in data:
        print(f"Error: {data['error']}")
        return

    print("=" * 70)
    print(BANNER)
    print("=" * 70)
    print(f"URL: {data['url']}")
    print(f"{STATUS_CODE}: {data['status_code']}")
    print("-" * 70)
    
    vp = data["viewport"]
    vp_status = STATUS_PASS if vp["present"] and vp["has_device_width"] else STATUS_FAIL
    print(f"{VIEWPORT_LABEL}: {vp_status}")
    if vp["content"]:
        print(f"  {VIEWPORT_CONTENT_LABEL}: {vp['content']}")
    
    lay = data["layout"]
    print(f"{TOUCH_TARGETS_LABEL}: {lay['total_touch_targets']}")
    print(f"{FIXED_WIDTHS_LABEL}: {lay['overflow_risk_count']}")
    print(f"{SMALL_FONTS_LABEL}: {lay['tiny_font_count']}")
    print(f"{TOUCH_ICON_LABEL}: {'OK' if lay['has_apple_touch_icon'] else 'AUSENTE'}")
    
    print("-" * 70)
    print(f"{SCORE_TITLE}: {data['score']}/100 [{data['overall_status']}]")
    
    if data["warnings"]:
        print("\nAlertas:")
        for w in data["warnings"]:
            print(f"  - {w}")
            
    print("=" * 70)
    print(f"{FOOTER_TOOL}: https://tools.tavardt.com/nz/mobile-seo-checker/")
    print(f"{FOOTER_PORTAL}: https://ag.tavardt.com/nz/")
    print("=" * 70)

def main():
    parser = argparse.ArgumentParser(description=DESC)
    parser.add_argument("target", help=TARGET_PROMPT)
    parser.add_argument("-json", "--json", action="store_true", help=JSON_HELP)
    args = parser.parse_args()

    results = analyze_mobile_seo(args.target)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_text_report(results)

if __name__ == "__main__":
    main()
