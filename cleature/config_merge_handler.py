"""
Handles merging of Cleature configuration dictionaries.

Supports deep merging of config values with type casting,
deduplicated list merging, recursive dict merging, and
fallback-safe overrides using predefined config schema.

© CodemasterUnited 2025
"""

from copy import deepcopy

# Define the expected types for each config key
CONFIG_TYPES = {
    'variables': dict,
    'excluded_dirs': list,
    'refresh_dist': bool,
    'debug': bool
}


def cast_value(key, value):
    """ Casts value to expected type from CONFIG_TYPES, if possible. """
    expected_type = CONFIG_TYPES.get(key)
    if expected_type is None:
        return value  # unknown keys are passed through

    if value is None:
        return None

    if isinstance(value, expected_type):
        return deepcopy(value)

    result = None
    try:
        if expected_type is list:
            result = [value] if not isinstance(value, list) else deepcopy(value)
        elif expected_type is dict:
            result = {} if not isinstance(value, dict) else deepcopy(value)
        else:
            result = expected_type(value)
    except Exception:  # pylint:disable=broad-exception-caught
        result = None

    return result


def merge_configs(*objs):
    """
    Merges multiple dicts using predefined type rules.
    - Casts to correct type using CONFIG_TYPES
    - Lists are merged with deduplication
    - Dicts are merged recursively
    - Scalars are overridden by later values
    - None never overrides a real value
    """
    result = {}

    for obj in objs:
        for key, val in obj.items():
            val = cast_value(key, val)

            if val is None:
                continue

            if key not in result or result[key] is None:
                result[key] = deepcopy(val)
            else:
                existing = result[key]
                if isinstance(existing, dict) and isinstance(val, dict):
                    result[key] = merge_configs(existing, val)
                elif isinstance(existing, list) and isinstance(val, list):
                    result[key] = existing + [v for v in val if v not in existing]
                else:
                    result[key] = deepcopy(val)

    return {k: v for k, v in result.items() if v is not None}
