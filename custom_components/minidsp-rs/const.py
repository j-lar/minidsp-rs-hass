DOMAIN = "minidsp"

# Default update interval for polling device status
SCAN_INTERVAL_SECONDS = 1

# Config entry options
CONF_MODEL = "model"
CONF_DEVICE_INDEX = "device_index"
CONF_LEVEL_INTERVAL = "level_interval"
CONF_DIRAC_UPGRADE = "dirac_upgrade"

# How often (seconds) level sensor pushes are forwarded to HA entities.
# 0.0 = no throttling (pass every WS message through).
DEFAULT_LEVEL_INTERVAL = 1.0

# Volume / gain boundaries (dB)
MASTER_VOLUME_MIN_DB = -127.0
MASTER_VOLUME_MAX_DB = 0.0
OUTPUT_GAIN_MIN_DB = -127.0
OUTPUT_GAIN_MAX_DB = 12.0

# ---------------------------------------------------------------------------
# Profile name constants
# ---------------------------------------------------------------------------
PROFILE_2X4HD = "2x4 HD"
PROFILE_DDRC24 = "DDRC-24"
PROFILE_SHD = "SHD / SHD Power"
PROFILE_DDRC88 = "DDRC-88"
PROFILE_FLEX = "Flex"
PROFILE_FLEXDL = "Flex DL"
PROFILE_MSHARC4X8 = "Flex Eight / mSHARC 4x8"
PROFILE_FLEXHTX = "Flex HTx"
PROFILE_10X10HD = "10x10 HD"
PROFILE_4X10HD = "4x10 HD"
PROFILE_NANODIGI2X8 = "NanoDigi 2x8"
PROFILE_CDSP8X12V2 = "C-DSP 8x12 v2"
PROFILE_2X4_LEGACY = "2x4 (legacy)"
PROFILE_GENERIC = "Generic/Basic"

# ---------------------------------------------------------------------------
# Device profiles
#
# Keys per profile:
#   sources         – list of {label, api} dicts; empty list = no source
#                     selection exposed in HA.
#   preset_count    – number of presets (always 4 for all known models).
#   has_dirac       – True if the hardware supports Dirac Live at all.
#   dirac_is_upgrade– True if Dirac is an optional paid upgrade rather than
#                     factory-installed.  The Dirac switch is only shown when
#                     has_dirac=True AND (not dirac_is_upgrade OR the user has
#                     set CONF_DIRAC_UPGRADE=True in the options flow).
#   has_compressor  – True if per-output compressor registers are wired in the
#                     minidsp-rs protocol definition for this device.
# ---------------------------------------------------------------------------

DEVICE_PROFILES: dict[str, dict] = {
    PROFILE_2X4HD: {
        "sources": [
            {"label": "Analog",  "api": "Analog"},
            {"label": "USB",     "api": "Usb"},
            {"label": "TOSLINK", "api": "Toslink"},
        ],
        "preset_count": 4,
        "has_dirac": True,
        "dirac_is_upgrade": True,
        "has_compressor": True,
    },
    PROFILE_DDRC24: {
        "sources": [
            {"label": "Analog",  "api": "Analog"},
            {"label": "USB",     "api": "Usb"},
            {"label": "TOSLINK", "api": "Toslink"},
        ],
        "preset_count": 4,
        "has_dirac": True,
        "dirac_is_upgrade": False,
        "has_compressor": True,
    },
    PROFILE_SHD: {
        "sources": [
            {"label": "Analog",  "api": "Analog"},
            {"label": "USB",     "api": "Usb"},
            {"label": "TOSLINK", "api": "Toslink"},
        ],
        "preset_count": 4,
        "has_dirac": True,
        "dirac_is_upgrade": False,
        "has_compressor": True,
    },
    PROFILE_DDRC88: {
        "sources": [
            {"label": "Analog",  "api": "Analog"},
            {"label": "USB",     "api": "Usb"},
            {"label": "TOSLINK", "api": "Toslink"},
        ],
        "preset_count": 4,
        "has_dirac": True,
        "dirac_is_upgrade": False,
        "has_compressor": True,
    },
    PROFILE_FLEX: {
        "sources": [
            {"label": "Analog",  "api": "Analog"},
            {"label": "TOSLINK", "api": "Toslink"},
            {"label": "SPDIF",   "api": "Spdif"},
            {"label": "USB",     "api": "Usb"},
        ],
        "preset_count": 4,
        "has_dirac": True,
        "dirac_is_upgrade": True,
        "has_compressor": True,
    },
    PROFILE_FLEXDL: {
        "sources": [
            {"label": "Analog",  "api": "Analog"},
            {"label": "TOSLINK", "api": "Toslink"},
            {"label": "SPDIF",   "api": "Spdif"},
            {"label": "USB",     "api": "Usb"},
        ],
        "preset_count": 4,
        "has_dirac": True,
        "dirac_is_upgrade": False,
        "has_compressor": True,
    },
    PROFILE_MSHARC4X8: {
        # Source selection is not exposed via the API for this device family.
        "sources": [],
        "preset_count": 4,
        "has_dirac": True,
        "dirac_is_upgrade": True,
        "has_compressor": True,
    },
    PROFILE_FLEXHTX: {
        "sources": [
            {"label": "Analog",  "api": "Analog"},
            {"label": "TOSLINK", "api": "Toslink"},
            {"label": "SPDIF",   "api": "Spdif"},
            {"label": "USB",     "api": "Usb"},
            # HDMI is not in the minidsp-rs Source enum; omitted intentionally.
        ],
        "preset_count": 4,
        "has_dirac": True,
        "dirac_is_upgrade": False,
        "has_compressor": True,
    },
    PROFILE_10X10HD: {
        "sources": [
            {"label": "TOSLINK", "api": "Toslink"},
            {"label": "SPDIF",   "api": "Spdif"},
        ],
        "preset_count": 4,
        "has_dirac": False,
        "dirac_is_upgrade": False,
        "has_compressor": False,
    },
    PROFILE_4X10HD: {
        "sources": [
            {"label": "SPDIF",   "api": "Spdif"},
            {"label": "TOSLINK", "api": "Toslink"},
            {"label": "AES/EBU", "api": "Aesebu"},
        ],
        "preset_count": 4,
        "has_dirac": False,
        "dirac_is_upgrade": False,
        "has_compressor": False,
    },
    PROFILE_NANODIGI2X8: {
        "sources": [
            {"label": "TOSLINK", "api": "Toslink"},
            {"label": "SPDIF",   "api": "Spdif"},
        ],
        "preset_count": 4,
        "has_dirac": False,
        "dirac_is_upgrade": False,
        "has_compressor": False,
    },
    PROFILE_CDSP8X12V2: {
        "sources": [
            {"label": "Analog",  "api": "Analog"},
            {"label": "TOSLINK", "api": "Toslink"},
            {"label": "SPDIF",   "api": "Spdif"},
        ],
        "preset_count": 4,
        "has_dirac": False,
        "dirac_is_upgrade": False,
        "has_compressor": True,
    },
    PROFILE_2X4_LEGACY: {
        "sources": [
            {"label": "TOSLINK", "api": "Toslink"},
            {"label": "SPDIF",   "api": "Spdif"},
        ],
        "preset_count": 4,
        "has_dirac": False,
        "dirac_is_upgrade": False,
        "has_compressor": False,
    },
    PROFILE_GENERIC: {
        # Catch-all: expose all known source values so unknown devices still
        # have a working source selector.
        "sources": [
            {"label": "Analog",  "api": "Analog"},
            {"label": "TOSLINK", "api": "Toslink"},
            {"label": "SPDIF",   "api": "Spdif"},
            {"label": "USB",     "api": "Usb"},
            {"label": "AES/EBU", "api": "Aesebu"},
            {"label": "RCA",     "api": "Rca"},
            {"label": "XLR",     "api": "Xlr"},
            {"label": "LAN",     "api": "Lan"},
            {"label": "I2S",     "api": "I2S"},
        ],
        "preset_count": 4,
        # Show Dirac for unknown devices since the API always reports it and
        # the user may have a Dirac-capable device we haven't profiled yet.
        "has_dirac": True,
        "dirac_is_upgrade": False,
        "has_compressor": False,
    },
}

# ---------------------------------------------------------------------------
# Hardware-ID based auto-detection
#
# Entries are (hw_id, dsp_version, profile_name).
# dsp_version=None is a wildcard that matches any dsp_version for that hw_id.
# The list is checked top-to-bottom; exact matches are tried before wildcards.
# ---------------------------------------------------------------------------
HW_ID_PROFILE_MAP: list[tuple[int, int | None, str]] = [
    (10, 100, PROFILE_2X4HD),
    (10, 101, PROFILE_DDRC24),
    (6,  95,  PROFILE_DDRC88),
    (14, None, PROFILE_SHD),
    (27, 100, PROFILE_FLEX),
    (27, 101, PROFILE_FLEXDL),
    (32, 113, PROFILE_FLEXHTX),
    (1,  51,  PROFILE_10X10HD),
    (1,  None, PROFILE_4X10HD),
    (4,  None, PROFILE_MSHARC4X8),
    (2,  54,  PROFILE_NANODIGI2X8),
    (11, 97,  PROFILE_CDSP8X12V2),
    (2,  22,  PROFILE_2X4_LEGACY),
]

# Legacy product-name substring fallback (lower-cased key → profile name).
PRODUCT_NAME_MODEL_MAP: dict[str, str] = {
    "2x4 hd":   PROFILE_2X4HD,
    "2x4hd":    PROFILE_2X4HD,
    "ddrc-24":  PROFILE_DDRC24,
    "ddrc24":   PROFILE_DDRC24,
    "ddrc-88":  PROFILE_DDRC88,
    "ddrc88":   PROFILE_DDRC88,
    "shd":      PROFILE_SHD,
    "flex dl":  PROFILE_FLEXDL,
    "flexdl":   PROFILE_FLEXDL,
    "flex htx": PROFILE_FLEXHTX,
    "flexhtx":  PROFILE_FLEXHTX,
    "flex":     PROFILE_FLEX,
    "10x10 hd": PROFILE_10X10HD,
    "10x10hd":  PROFILE_10X10HD,
    "4x10 hd":  PROFILE_4X10HD,
    "4x10hd":   PROFILE_4X10HD,
    "nanodigi": PROFILE_NANODIGI2X8,
    "c-dsp 8x12": PROFILE_CDSP8X12V2,
    "msharc":   PROFILE_MSHARC4X8,
    "nanoshrc": PROFILE_MSHARC4X8,
}


def profile_from_hw_id(hw_id: int, dsp_version: int) -> str | None:
    """Return the profile name for a given hw_id/dsp_version, or None."""
    # Exact match first
    for h, d, p in HW_ID_PROFILE_MAP:
        if h == hw_id and d == dsp_version:
            return p
    # Wildcard match (dsp_version=None)
    for h, d, p in HW_ID_PROFILE_MAP:
        if h == hw_id and d is None:
            return p
    return None


def validate_profile(profile: dict) -> bool:
    sources = profile.get("sources")
    preset_count = profile.get("preset_count")
    # sources may be an empty list (devices with no API-controllable source)
    if not isinstance(sources, list):
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
