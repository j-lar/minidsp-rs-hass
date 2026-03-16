DOMAIN = "minidsp"

# Default update interval for polling device status
SCAN_INTERVAL_SECONDS = 1

# Config entry options
CONF_MODEL = "model"
CONF_DEVICE_INDEX = "device_index"

# Volume / gain boundaries (dB)
MASTER_VOLUME_MIN_DB = -127.0
MASTER_VOLUME_MAX_DB = 0.0
OUTPUT_GAIN_MIN_DB = -127.0
OUTPUT_GAIN_MAX_DB = 12.0

PROFILE_2X4HD = "2x4HD"
PROFILE_GENERIC = "Generic/Basic"

# TODO: Multi-device support — CONF_DEVICE_INDEX is stored in config entries and passed
#       to MiniDSPAPI, but each config entry still represents one device_index against
#       one daemon URL. A full multi-device UI (auto-enumerate all devices and offer one
#       entry per device) is deferred for future work.
#
# Auto-detection of device model from /devices is already implemented in __init__.py.
DEVICE_PROFILES = {
    PROFILE_2X4HD: {
        "sources": [
            {"label": "Analog", "api": "Analog"},
            {"label": "USB", "api": "Usb"},
            {"label": "TOSLINK", "api": "Toslink"},
        ],
        "preset_count": 4,
    },
    PROFILE_GENERIC: {
        "sources": [
            {"label": "Analog", "api": "Analog"},
            {"label": "Toslink", "api": "Toslink"},
            {"label": "Spdif", "api": "Spdif"},
            {"label": "Usb", "api": "Usb"},
            {"label": "Aesebu", "api": "Aesebu"},
            {"label": "Rca", "api": "Rca"},
            {"label": "Xlr", "api": "Xlr"},
            {"label": "Lan", "api": "Lan"},
            {"label": "I2S", "api": "I2S"},
        ],
        "preset_count": 4,
    },
}

# Product name heuristics for auto-detection.
PRODUCT_NAME_MODEL_MAP = {
    "2x4 hd": PROFILE_2X4HD,
    "2x4hd": PROFILE_2X4HD,
}


def validate_profile(profile: dict) -> bool:
    sources = profile.get("sources")
    preset_count = profile.get("preset_count")
    if not isinstance(sources, list) or not sources:
        return False
    for source in sources:
        if not isinstance(source, dict):
            return False
        if "label" not in source or "api" not in source:
            return False
        if not isinstance(source["label"], str) or not isinstance(source["api"], str):
            return False
    if not isinstance(preset_count, int) or preset_count <= 0:
        return False
    return True


def build_source_maps(profile: dict) -> tuple[dict[str, str], dict[str, str]]:
    label_to_api = {s["label"]: s["api"] for s in profile.get("sources", [])}
    api_to_label = {s["api"]: s["label"] for s in profile.get("sources", [])}
    return label_to_api, api_to_label


def build_preset_maps(profile: dict) -> tuple[dict[str, int], dict[int, str]]:
    count = int(profile.get("preset_count", 4))
    label_to_index = {f"Preset {i + 1}": i for i in range(count)}
    index_to_label = {i: f"Preset {i + 1}" for i in range(count)}
    return label_to_index, index_to_label
