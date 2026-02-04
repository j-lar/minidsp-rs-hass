from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_const_module():
    const_path = (
        Path(__file__).resolve().parents[1]
        / "custom_components"
        / "minidsp-rs"
        / "const.py"
    )
    spec = spec_from_file_location("minidsp_rs_const", const_path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


const = _load_const_module()


def test_profiles_are_valid():
    for profile in const.DEVICE_PROFILES.values():
        assert const.validate_profile(profile)


def test_source_maps_round_trip():
    profile = const.DEVICE_PROFILES[const.PROFILE_2X4HD]
    label_to_api, api_to_label = const.build_source_maps(profile)
    for label, api in label_to_api.items():
        assert api_to_label[api] == label


def test_preset_maps_round_trip():
    profile = const.DEVICE_PROFILES[const.PROFILE_GENERIC]
    label_to_index, index_to_label = const.build_preset_maps(profile)
    for label, index in label_to_index.items():
        assert index_to_label[index] == label
