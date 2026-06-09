"""Model package helpers for the Deep Learning NLP Political Speeches project.

This module avoids importing heavy dependencies at package import time and
provides a convenience `load_model` helper to load a trained model and its
tokenizer from a saved directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple


def _import_model_module():
	"""Import the concrete model module on demand."""
	import importlib

	return importlib.import_module(".model", __package__)


def get_model_class():
	"""Return the `RobertaTrumpClassifier` class and `build_tokenizer` callable.

	Import occurs lazily to avoid issues with import-time side effects.
	"""
	mod = _import_model_module()
	return mod.RobertaTrumpClassifier, mod.build_tokenizer


def load_model(save_dir: str | Path, model_name: str = "roberta-base", device: Optional[str] = None):
	"""Load a trained model and tokenizer from `save_dir`.

	Returns (model, tokenizer, device).
	"""
	from transformers import AutoTokenizer
	import torch

	save_dir = Path(save_dir)
	RobertaTrumpClassifier, build_tokenizer = get_model_class()

	if device is None:
		device = "cuda" if torch.cuda.is_available() else "cpu"

	device = torch.device(device)

	# Try to load tokenizer/model from save_dir; fall back to fresh tokenizer/model
	if save_dir.exists() and (save_dir / "model.pt").exists():
		tokenizer = AutoTokenizer.from_pretrained(str(save_dir))
		model = RobertaTrumpClassifier(model_name=model_name)
		state = torch.load(str(save_dir / "model.pt"), map_location=device)
		load_result = model.load_state_dict(state, strict=False)
		missing_keys = list(load_result.missing_keys)
		unexpected_keys = list(load_result.unexpected_keys)
		if missing_keys or unexpected_keys:
			message_lines = [
				"Checkpoint does not match RobertaTrumpClassifier.",
				f"save_dir: {save_dir}",
				"This usually means the wrong checkpoint type is being loaded (for example, a Hugging Face LM checkpoint instead of the saved classifier state_dict).",
			]
			if missing_keys:
				message_lines.append("Missing keys: " + ", ".join(missing_keys))
			if unexpected_keys:
				message_lines.append("Unexpected keys: " + ", ".join(unexpected_keys))
			raise RuntimeError("\n".join(message_lines))
		model.to(device).eval()
	else:
		tokenizer = build_tokenizer(model_name)
		model = RobertaTrumpClassifier(model_name=model_name)
		model.to(device).eval()

	return model, tokenizer, device


__all__ = ["get_model_class", "load_model"]