"""Tests for the DeepMIMO channel loader and its integration with the pipeline."""

import numpy as np
import pytest
from scipy.io import savemat

from neuromimo.config import EstimationAlgorithm, SimulationConfig
from neuromimo.estimation.trainer import generate_channel_dataset
from neuromimo.evaluation.deepmimo_cli import run_deepmimo_sweep
from neuromimo.wireless.channel import WirelessChannel
from neuromimo.wireless.deepmimo import DeepMIMOChannelSet
from neuromimo.wireless.simulation import MIMOSimulationPipeline


def make_deepmimo_like_channels(
    num_users: int = 30,
    num_rx_ant: int = 2,
    num_tx_ant: int = 4,
    num_subcarriers: int = 128,
    num_taps: int = 6,
    num_empty_users: int = 3,
    seed: int = 0,
) -> np.ndarray:
    """Builds an array shaped like DeepMIMO OFDM output, with a path-loss scale and empty users."""
    rng = np.random.RandomState(seed)
    pdp = np.exp(-np.arange(num_taps) / 2.0)
    pdp /= pdp.sum()
    taps = (rng.normal(size=(num_users, num_rx_ant, num_tx_ant, num_taps))
            + 1j * rng.normal(size=(num_users, num_rx_ant, num_tx_ant, num_taps))) * np.sqrt(pdp / 2)
    channels = np.fft.fft(taps, n=num_subcarriers, axis=-1) * 1e-5  # strong path loss
    channels[:num_empty_users] = 0.0
    return channels.astype(np.complex64)


def test_loader_selects_antennas_subcarriers_and_drops_empty_users():
    raw = make_deepmimo_like_channels()
    channel_set = DeepMIMOChannelSet(raw)

    assert channel_set.H.shape == (27, 2, 2, 64)
    assert channel_set.num_dropped_users == 3
    assert list(channel_set.user_indices[:2]) == [3, 4]
    # Every channel is normalised to unit average power despite the path loss
    power = np.mean(np.abs(channel_set.H) ** 2, axis=(1, 2, 3))
    np.testing.assert_allclose(power, 1.0, rtol=1e-6)


def test_loader_keeps_exact_subcarriers_when_grid_matches():
    raw = make_deepmimo_like_channels(num_subcarriers=64, num_empty_users=0)
    channel_set = DeepMIMOChannelSet(raw)
    expected = raw[:, :2, :2, :].astype(np.complex128)
    expected /= np.sqrt(np.mean(np.abs(expected) ** 2, axis=(1, 2, 3)))[:, None, None, None]
    np.testing.assert_allclose(channel_set.H, expected, rtol=1e-5)


@pytest.mark.parametrize("ext", [".npy", ".npz", ".mat"])
def test_from_file_reads_all_supported_formats(tmp_path, ext):
    raw = make_deepmimo_like_channels()
    path = tmp_path / f"channels{ext}"
    if ext == ".npy":
        np.save(path, raw)
    elif ext == ".npz":
        np.savez(path, channel=raw)
    else:
        savemat(path, {"channel": raw})

    channel_set = DeepMIMOChannelSet.from_file(str(path))
    assert channel_set.num_channels == 27


def test_from_deepmimo_v3_dataset_structure():
    raw = make_deepmimo_like_channels()
    dataset = [{"user": {"channel": raw}}]
    assert DeepMIMOChannelSet.from_deepmimo_v3(dataset).num_channels == 27


def test_loader_rejects_unusable_arrays():
    with pytest.raises(ValueError, match="antennas"):
        DeepMIMOChannelSet(make_deepmimo_like_channels(num_rx_ant=1))
    with pytest.raises(ValueError, match="subcarriers"):
        DeepMIMOChannelSet(make_deepmimo_like_channels(num_subcarriers=32))
    with pytest.raises(ValueError, match="real-valued"):
        DeepMIMOChannelSet(np.ones((4, 2, 2, 64)))
    with pytest.raises(ValueError, match="time axis"):
        DeepMIMOChannelSet(np.ones((4, 2, 2, 64, 3), dtype=complex))


def test_split_by_user_has_no_overlap():
    channel_set = DeepMIMOChannelSet(make_deepmimo_like_channels(num_users=60))
    train, val, test = channel_set.split(random_seed=1)
    ids = [set(part.user_indices) for part in (train, val, test)]
    assert sum(len(i) for i in ids) == channel_set.num_channels
    assert not (ids[0] & ids[1]) and not (ids[0] & ids[2]) and not (ids[1] & ids[2])


def test_estimated_pdp_matches_generating_profile():
    channel_set = DeepMIMOChannelSet(
        make_deepmimo_like_channels(num_users=400, num_subcarriers=64, num_empty_users=0)
    )
    pdp = channel_set.estimate_pdp()
    assert pdp.shape == (64,)
    assert pdp.sum() == pytest.approx(1.0)
    # Energy sits in the first 6 taps, decaying like the generating profile
    assert pdp[:6].sum() > 0.99
    assert pdp[0] > pdp[2] > pdp[5]


def test_wireless_channel_draws_from_channel_set():
    channel_set = DeepMIMOChannelSet(make_deepmimo_like_channels())
    channel = WirelessChannel(random_seed=3, channel_set=channel_set)
    _, H = channel.generate_channel_response()
    assert any(np.allclose(H, candidate) for candidate in channel_set.H)
    np.testing.assert_allclose(channel.pdp, channel_set.estimate_pdp())


def test_pipeline_runs_on_deepmimo_channels():
    channel_set = DeepMIMOChannelSet(make_deepmimo_like_channels())
    perfect = MIMOSimulationPipeline(
        SimulationConfig(algorithm=EstimationAlgorithm.PERFECT, snr_db=30.0), channel_set=channel_set
    ).run_single_shot()
    assert perfect["nmse"] == 0.0

    mmse = MIMOSimulationPipeline(
        SimulationConfig(algorithm=EstimationAlgorithm.MMSE, snr_db=10.0), channel_set=channel_set
    ).run_single_shot()
    assert np.isfinite(mmse["nmse_db"])


def test_dataset_generation_uses_channel_set():
    channel_set = DeepMIMOChannelSet(make_deepmimo_like_channels())
    X, Y, _ = generate_channel_dataset(num_samples=5, random_seed=0, channel_set=channel_set)
    assert X.shape == Y.shape == (5, 512)
    targets = Y[:, :256] + 1j * Y[:, 256:]
    flat = channel_set.H.reshape(channel_set.num_channels, -1)
    for row in targets:
        assert np.min(np.abs(flat - row).max(axis=1)) < 1e-5


def test_sweep_gives_identical_channels_to_every_estimator():
    channel_set = DeepMIMOChannelSet(make_deepmimo_like_channels())
    records = run_deepmimo_sweep(
        channel_set, snr_points=[0.0, 20.0], num_trials=2, algorithms=("LS", "MMSE", "PERFECT")
    )
    assert set(records) == {"LS", "MMSE", "PERFECT"}
    for algo in records:
        assert [r["snr_db"] for r in records[algo]] == [0.0, 20.0]
    # Same channels and noise: the genie bound has no estimation error
    assert all(r["nmse_db"] <= -100 for r in records["PERFECT"])
    assert records["LS"][1]["nmse_db"] < records["LS"][0]["nmse_db"]
