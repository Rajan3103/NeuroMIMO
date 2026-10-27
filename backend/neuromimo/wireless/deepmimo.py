"""Loader for ray-traced DeepMIMO channels.

DeepMIMO (https://deepmimo.net) produces frequency-domain MIMO channels from
ray-tracing of realistic scenes. Both DeepMIMO v3 (``dataset[bs]['user']['channel']``)
and v4 (``dataset.compute_channels()``) return arrays shaped

    (num_users, num_rx_ant, num_tx_ant, num_subcarriers)

This module turns such an array into channels the NeuroMIMO pipeline can use:
    1. Keep the first ``num_rx`` x ``num_tx`` antennas (2x2 by default).
    2. Map the subcarriers onto the ``fft_size``-point OFDM grid.
    3. Drop users with no propagation paths (all-zero channels).
    4. Normalise every user's channel to unit average power, matching the
       synthetic Rayleigh channels, so SNR and DNN input scales are comparable.

The DeepMIMO package itself is not required: export the channel array with
``numpy.save`` (or ``scipy.io.savemat``) and load the file here.
"""

import os
from typing import Any, Optional, Tuple

import numpy as np


class DeepMIMOChannelSet:
    """A set of normalised DeepMIMO channel frequency responses.

    Attributes:
        H: Shape (num_channels, num_rx, num_tx, fft_size) complex channels.
        user_indices: Index of each kept channel in the original DeepMIMO user list.
        num_dropped_users: Users removed because they had no propagation paths.
    """

    def __init__(
        self,
        channels: np.ndarray,
        num_rx: int = 2,
        num_tx: int = 2,
        fft_size: int = 64,
    ) -> None:
        channels = np.asarray(channels)
        if channels.ndim == 5:
            raise ValueError(
                "Channel array has a time axis (5 dimensions). Export a single snapshot "
                "with shape (users, rx_antennas, tx_antennas, subcarriers)."
            )
        if channels.ndim != 4:
            raise ValueError(
                f"Expected a 4-D channel array (users, rx_antennas, tx_antennas, subcarriers), "
                f"got shape {channels.shape}."
            )
        if not np.iscomplexobj(channels):
            raise ValueError(
                "Channel array is real-valued. Export frequency-domain channels "
                "(DeepMIMO OFDM channels), which are complex."
            )

        n_users, n_rx_ant, n_tx_ant, n_sub = channels.shape
        if n_rx_ant < num_rx or n_tx_ant < num_tx:
            raise ValueError(
                f"Need at least {num_rx} receive and {num_tx} transmit antennas, but the file has "
                f"{n_rx_ant} rx x {n_tx_ant} tx. In DeepMIMO, set the user (UE) and base station "
                f"antenna shapes so each side has at least 2 antennas."
            )
        if n_sub < fft_size:
            raise ValueError(
                f"Need at least {fft_size} subcarriers, but the file has {n_sub}. "
                f"Generate DeepMIMO channels with {fft_size} or more subcarriers."
            )

        selected = channels[:, :num_rx, :num_tx, :].astype(np.complex128)
        if n_sub > fft_size:
            # Evenly spaced subcarriers keep the full bandwidth on the smaller grid
            sub_idx = np.round(np.linspace(0, n_sub - 1, fft_size)).astype(int)
            selected = selected[..., sub_idx]

        # Users without any path have an all-zero channel and carry no information
        power = np.mean(np.abs(selected) ** 2, axis=(1, 2, 3))
        keep = power > 1e-30
        if not np.any(keep):
            raise ValueError("Every user in the file has an all-zero channel (no propagation paths).")

        self.user_indices = np.flatnonzero(keep)
        self.num_dropped_users = int(n_users - keep.sum())
        self.H = selected[keep] / np.sqrt(power[keep])[:, None, None, None]
        self.num_rx = num_rx
        self.num_tx = num_tx
        self.fft_size = fft_size

    @property
    def num_channels(self) -> int:
        return int(self.H.shape[0])

    @classmethod
    def from_file(
        cls,
        path: str,
        key: Optional[str] = None,
        num_rx: int = 2,
        num_tx: int = 2,
        fft_size: int = 64,
    ) -> "DeepMIMOChannelSet":
        """Loads channels from a .npy, .npz or .mat file.

        Args:
            path: File holding a (users, rx_antennas, tx_antennas, subcarriers) complex array.
            key: Array name inside a .npz or .mat file. Defaults to "channel" or
                "channels" if present, otherwise the only array in the file.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Channel file not found: {path}")

        ext = os.path.splitext(path)[1].lower()
        if ext == ".npy":
            channels = np.load(path, allow_pickle=False)
        elif ext == ".npz":
            with np.load(path, allow_pickle=False) as data:
                channels = data[_pick_key(list(data.keys()), key, path)]
        elif ext == ".mat":
            from scipy.io import loadmat

            data = {k: v for k, v in loadmat(path).items() if not k.startswith("__")}
            channels = data[_pick_key(list(data.keys()), key, path)]
        else:
            raise ValueError(f"Unsupported file type '{ext}'. Use .npy, .npz or .mat.")

        return cls(channels, num_rx=num_rx, num_tx=num_tx, fft_size=fft_size)

    @classmethod
    def from_deepmimo_v3(
        cls,
        dataset: Any,
        bs_index: int = 0,
        num_rx: int = 2,
        num_tx: int = 2,
        fft_size: int = 64,
    ) -> "DeepMIMOChannelSet":
        """Builds the set straight from a DeepMIMO v3 ``generate_data`` result.

        For DeepMIMO v4, call ``dataset.compute_channels(params)`` and pass the
        returned array to the constructor instead.
        """
        channels = dataset[bs_index]["user"]["channel"]
        return cls(channels, num_rx=num_rx, num_tx=num_tx, fft_size=fft_size)

    def estimate_pdp(self) -> np.ndarray:
        """Average power delay profile over all channels, normalised to sum to 1.

        Returned with one entry per delay tap (fft_size taps), so the LMMSE
        estimator can use the empirical frequency correlation of the scene.
        """
        h_time = np.fft.ifft(self.H, axis=-1)
        pdp = np.mean(np.abs(h_time) ** 2, axis=(0, 1, 2))
        return pdp / np.sum(pdp)

    def split(
        self,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        random_seed: int = 42,
    ) -> Tuple["DeepMIMOChannelSet", "DeepMIMOChannelSet", "DeepMIMOChannelSet"]:
        """Splits by user into train/validation/test sets with no user in two sets."""
        indices = np.random.RandomState(random_seed).permutation(self.num_channels)
        n_train = int(self.num_channels * train_ratio)
        n_val = int(self.num_channels * val_ratio)
        parts = (
            indices[:n_train],
            indices[n_train : n_train + n_val],
            indices[n_train + n_val :],
        )
        return tuple(self._subset(part) for part in parts)

    def sample(self, rng: np.random.RandomState) -> np.ndarray:
        """Returns one randomly chosen channel, shape (num_rx, num_tx, fft_size)."""
        return self.H[rng.randint(self.num_channels)].copy()

    def _subset(self, indices: np.ndarray) -> "DeepMIMOChannelSet":
        subset = object.__new__(DeepMIMOChannelSet)
        subset.H = self.H[indices]
        subset.user_indices = self.user_indices[indices]
        subset.num_dropped_users = 0
        subset.num_rx = self.num_rx
        subset.num_tx = self.num_tx
        subset.fft_size = self.fft_size
        return subset


def _pick_key(keys: list, key: Optional[str], path: str) -> str:
    if key is not None:
        if key not in keys:
            raise KeyError(f"Array '{key}' not found in {path}. Available: {keys}")
        return key
    for default in ("channel", "channels"):
        if default in keys:
            return default
    if len(keys) == 1:
        return keys[0]
    raise KeyError(f"{path} holds several arrays {keys}; choose one with key=...")
