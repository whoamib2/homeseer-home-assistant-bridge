from __future__ import annotations
from time import time
from .bridge_stats import ensure_stats
from .device_model import classify_device
CACHE_SECONDS = 300
MAX_SAMPLES = 25

def _clean(value):
    return '' if value is None else str(value).strip()

def _device_name(device: dict, ref) -> str:
    parts = [_clean(device.get('location2')), _clean(device.get('location')), _clean(device.get('name'))]
    return ' '.join(part for part in parts if part) or f'HomeSeer Ref {ref}'

def _normalize_name(name: str) -> str:
    return ' '.join(str(name or '').lower().replace('-', ' ').replace('_', ' ').split())

def _looks_like_battery(device: dict) -> bool:
    text = ' '.join(str(device.get(k) or '') for k in ('name','device_type','device_type_string','status')).lower()
    return 'battery' in text

def _is_hidden_or_disabled_candidate(device: dict) -> bool:
    text = ' '.join(str(device.get(k) or '') for k in ('name','location','location2','interface','device_type','device_type_string')).lower()
    return any(term in text for term in ('test','debug','unused','old ','deprecated'))

def update_management_report(data: dict, *, force: bool = False) -> dict:
    stats = ensure_stats(data)
    now = time()
    report = stats.get('management_report')
    last = stats.get('management_report_timestamp')
    if report and last and not force and now - float(last) < CACHE_SECONDS:
        return report
    state = data.get('state') or {}
    name_refs = {}
    samples = {k: [] for k in ('duplicate_name_groups','missing_area','low_confidence','battery_named','cleanup_candidates','naming_candidates','class_suggestions','area_suggestions')}
    counts = {k: 0 for k in ('duplicate_name_groups','missing_area','low_confidence','battery_named','cleanup_candidates','naming_candidates','class_suggestions','area_suggestions')}
    counts['total_devices'] = len(state)
    for ref, device in state.items():
        model = classify_device(device, ref)
        name = _device_name(device, ref)
        norm = _normalize_name(name)
        if norm:
            name_refs.setdefault(norm, []).append(ref)
        if not model.suggested_area:
            counts['missing_area'] += 1
            if len(samples['missing_area']) < MAX_SAMPLES: samples['missing_area'].append({'ref': ref, 'name': name})
        if model.confidence < 70 or model.category == 'other':
            counts['low_confidence'] += 1
            if len(samples['low_confidence']) < MAX_SAMPLES: samples['low_confidence'].append({'ref': ref, 'name': name, 'category': model.category, 'confidence': model.confidence})
        if _looks_like_battery(device) and model.category != 'sensor':
            counts['battery_named'] += 1
            if len(samples['battery_named']) < MAX_SAMPLES: samples['battery_named'].append({'ref': ref, 'name': name, 'suggestion': 'Review as battery sensor'})
        if _is_hidden_or_disabled_candidate(device):
            counts['cleanup_candidates'] += 1
            if len(samples['cleanup_candidates']) < MAX_SAMPLES: samples['cleanup_candidates'].append({'ref': ref, 'name': name, 'suggestion': 'Review for disable/ignore'})
        raw_name = _clean(device.get('name'))
        if raw_name and model.suggested_area and model.suggested_area.lower() not in raw_name.lower():
            counts['naming_candidates'] += 1
            if len(samples['naming_candidates']) < MAX_SAMPLES: samples['naming_candidates'].append({'ref': ref, 'current': raw_name, 'suggested': name, 'reason': 'Add HomeSeer location context'})
        if model.category != 'other' and model.confidence >= 70:
            counts['class_suggestions'] += 1
            if len(samples['class_suggestions']) < MAX_SAMPLES: samples['class_suggestions'].append({'ref': ref, 'name': name, 'suggested_category': model.category, 'confidence': model.confidence})
        if model.suggested_area:
            counts['area_suggestions'] += 1
            if len(samples['area_suggestions']) < MAX_SAMPLES: samples['area_suggestions'].append({'ref': ref, 'name': name, 'suggested_area': model.suggested_area, 'suggested_floor': model.location2})
    for norm, refs in name_refs.items():
        if len(refs) > 1:
            counts['duplicate_name_groups'] += 1
            if len(samples['duplicate_name_groups']) < MAX_SAMPLES: samples['duplicate_name_groups'].append({'normalized_name': norm, 'refs': refs[:10], 'count': len(refs)})
    report = {'generated_at': now, 'cache_seconds': CACHE_SECONDS, 'counts': counts, 'samples': samples, 'note': 'Advisory only. v3.7.0 does not automatically rename, disable, or move devices.'}
    stats['management_report'] = report
    stats['management_report_timestamp'] = now
    return report

def get_management_report(data: dict) -> dict:
    stats = ensure_stats(data)
    return stats.get('management_report') or update_management_report(data, force=True)
