DOMAIN = "minidsp"

# Config entry options
CONF_MODEL = "model"

PROFILE_2X4HD = "2x4HD"
PROFILE_GENERIC = "Generic/Basic"

# TODO: Multi-device support — MiniDSPAPI currently hardcodes device_index=0.
#       Implementing this requires config flow changes to let users pick a device index
#       and to create one config entry per device. Deferred for future work.
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


def build_source_maps(profile: dict) -> tuple[dict[str, str], dict[str, str]]:
    label_to_api = {s["label"]: s["api"] for s in profile.get("sources", [])}
    api_to_label = {s["api"]: s["label"] for s in profile.get("sources", [])}
    return label_to_api, api_to_label


def build_preset_maps(profile: dict) -> tuple[dict[str, int], dict[int, str]]:
    count = int(profile.get("preset_count", 4))
    label_to_index = {f"Preset {i + 1}": i for i in range(count)}
    index_to_label = {i: f"Preset {i + 1}" for i in range(count)}
    return label_to_index, index_to_label
