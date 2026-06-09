"""Train a RoBERTa classifier for the speech dataset.

This script uses the project's existing dataloader, tokenizes batches on the fly,
fine-tunes RoBERTa, and saves the trained model artifacts.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import torch
from torch import nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
	sys.path.insert(0, str(SRC_ROOT))

from data.dataloader import get_data_loaders  # noqa: E402
from models.model import RobertaTrumpClassifier, build_tokenizer  # noqa: E402


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Train a RoBERTa speech classifier.")
	parser.add_argument("--base-path", type=str, default=str(SRC_ROOT / "data" / "us2020data" / "data_clean"))
	parser.add_argument("--file-format", type=str, default="jsonl", choices=("jsonl", "csv", "tsv", "parquet"))
	parser.add_argument("--text-column", type=str, default="CleanText")
	parser.add_argument("--label-column", type=str, default="POTUS")
	parser.add_argument("--positive-label", type=str, default="Donald Trump")
	parser.add_argument("--candidates", nargs="*", default=["Joe Biden", "Donald Trump"])
	parser.add_argument("--batch-size", type=int, default=8)
	parser.add_argument("--epochs", type=int, default=3)
	parser.add_argument("--learning-rate", type=float, default=2e-5)
	parser.add_argument("--weight-decay", type=float, default=0.01)
	parser.add_argument("--patience", type=int, default=2)
	parser.add_argument("--min-delta", type=float, default=1e-4)
	parser.add_argument("--max-grad-norm", type=float, default=1.0)
	parser.add_argument("--max-length", type=int, default=256)
	parser.add_argument("--model-name", type=str, default="roberta-base")
	parser.add_argument("--freeze-encoder", action="store_true")
	parser.add_argument("--resume-from", type=str, default=None, help="Path to a previously saved classifier state_dict (.pt) to resume from.")
	parser.add_argument("--seed", type=int, default=42)
	parser.add_argument("--num-workers", type=int, default=0)
	parser.add_argument("--save-dir", type=str, default=str(PROJECT_ROOT / "outputs" / "roberta_trump"))
	return parser.parse_args()


def set_seed(seed: int) -> None:
	random.seed(seed)
	np.random.seed(seed)
	torch.manual_seed(seed)
	if torch.cuda.is_available():
		torch.cuda.manual_seed_all(seed)


def tokenize_texts(tokenizer, texts: Iterable[str], max_length: int, device: torch.device) -> dict[str, torch.Tensor]:
	encoded = tokenizer(
		list(texts),
		padding=True,
		truncation=True,
		max_length=max_length,
		return_tensors="pt",
	)
	return {key: value.to(device) for key, value in encoded.items()}


def run_epoch(
	model: nn.Module,
	loader,
	tokenizer,
	optimizer: AdamW | None,
	device: torch.device,
	max_length: int,
	max_grad_norm: float = 1.0,
) -> dict[str, float]:
	is_train = optimizer is not None
	model.train(is_train)
	criterion = nn.CrossEntropyLoss()
	loss_sum = 0.0
	correct = 0
	total = 0

	for batch in loader:
		texts, labels = batch
		inputs = tokenize_texts(tokenizer, texts, max_length=max_length, device=device)
		labels = torch.as_tensor(labels, dtype=torch.long, device=device)

		if is_train:
			optimizer.zero_grad(set_to_none=True)

		outputs = model(**inputs)
		loss = criterion(outputs.logits, labels)

		if is_train:
			loss.backward()
			torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=max_grad_norm)
			optimizer.step()

		batch_size = labels.size(0)
		loss_sum += loss.item() * batch_size
		predictions = outputs.logits.argmax(dim=-1)
		correct += (predictions == labels).sum().item()
		total += batch_size

	return {
		"loss": loss_sum / max(total, 1),
		"accuracy": correct / max(total, 1),
	}


def save_artifacts(model: nn.Module, tokenizer, save_dir: Path, metrics: dict[str, float]) -> None:
	save_dir.mkdir(parents=True, exist_ok=True)
	torch.save(model.state_dict(), save_dir / "model.pt")
	tokenizer.save_pretrained(save_dir)
	with (save_dir / "metrics.json").open("w", encoding="utf-8") as handle:
		json.dump(metrics, handle, indent=2)


def load_resume_checkpoint(model: nn.Module, checkpoint_path: Path, device: torch.device) -> None:
	if not checkpoint_path.exists():
		raise FileNotFoundError(f"resume checkpoint not found: {checkpoint_path}")
	state = torch.load(str(checkpoint_path), map_location=device)
	load_result = model.load_state_dict(state, strict=False)
	missing_keys = list(load_result.missing_keys)
	unexpected_keys = list(load_result.unexpected_keys)
	if missing_keys or unexpected_keys:
		message_lines = [
			"Resume checkpoint does not match RobertaTrumpClassifier.",
			f"checkpoint: {checkpoint_path}",
			"Use a checkpoint produced by this trainer's `torch.save(model.state_dict(), ...)` output.",
		]
		if missing_keys:
			message_lines.append("Missing keys: " + ", ".join(missing_keys))
		if unexpected_keys:
			message_lines.append("Unexpected keys: " + ", ".join(unexpected_keys))
		raise RuntimeError("\n".join(message_lines))


def main() -> None:
	args = parse_args()
	set_seed(args.seed)
	device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

	tokenizer = build_tokenizer(args.model_name)
	model = RobertaTrumpClassifier(model_name=args.model_name, freeze_encoder=args.freeze_encoder).to(device)
	if args.resume_from is not None:
		load_resume_checkpoint(model, Path(args.resume_from), device)
		print(f"Resumed classifier weights from {args.resume_from}")

	train_loader, test_loader, dev_loader = get_data_loaders(
		base_path=args.base_path,
		batch_size=args.batch_size,
		text_column=args.text_column,
		label_column=args.label_column,
		candidates=args.candidates,
		file_format=args.file_format,
		seed=args.seed,
		num_workers=args.num_workers,
		shuffle_train=True,
	)

	optimizer = AdamW(
		(parameter for parameter in model.parameters() if parameter.requires_grad),
		lr=args.learning_rate,
		weight_decay=args.weight_decay,
	)
	scheduler = ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=1)

	best_dev_loss = float("inf")
	best_metrics: dict[str, float] = {}
	best_state_dict = None
	patience_counter = 0
	run_epoch.max_grad_norm = args.max_grad_norm

	for epoch in range(1, args.epochs + 1):
		train_metrics = run_epoch(
			model=model,
			loader=train_loader,
			tokenizer=tokenizer,
			optimizer=optimizer,
			device=device,
			max_length=args.max_length,
			max_grad_norm=args.max_grad_norm,
		)
		dev_metrics = run_epoch(
			model=model,
			loader=dev_loader,
			tokenizer=tokenizer,
			optimizer=None,
			device=device,
			max_length=args.max_length,
			max_grad_norm=args.max_grad_norm,
		)

		print(
			f"Epoch {epoch}/{args.epochs} | "
			f"train_loss={train_metrics['loss']:.4f} train_acc={train_metrics['accuracy']:.4f} | "
			f"dev_loss={dev_metrics['loss']:.4f} dev_acc={dev_metrics['accuracy']:.4f}"
		)

		scheduler.step(dev_metrics["loss"])

		if dev_metrics["loss"] < (best_dev_loss - args.min_delta):
			best_dev_loss = dev_metrics["loss"]
			best_metrics = {
				"train_loss": train_metrics["loss"],
				"train_accuracy": train_metrics["accuracy"],
				"dev_loss": dev_metrics["loss"],
				"dev_accuracy": dev_metrics["accuracy"],
			}
			best_state_dict = {key: value.cpu().clone() for key, value in model.state_dict().items()}
			patience_counter = 0
		else:
			patience_counter += 1
			if patience_counter >= args.patience:
				print(f"Early stopping triggered after {epoch} epochs (best dev_loss={best_dev_loss:.4f}).")
				break

	if best_state_dict is not None:
		model.load_state_dict(best_state_dict)

	test_metrics = run_epoch(
		model=model,
		loader=test_loader,
		tokenizer=tokenizer,
		optimizer=None,
		device=device,
		max_length=args.max_length,
		max_grad_norm=args.max_grad_norm,
	)

	final_metrics = {
		**best_metrics,
		"test_loss": test_metrics["loss"],
		"test_accuracy": test_metrics["accuracy"],
		"model_name": args.model_name,
		"max_length": args.max_length,
		"batch_size": args.batch_size,
		"epochs": args.epochs,
	}
	print(json.dumps(final_metrics, indent=2))
	save_artifacts(model, tokenizer, Path(args.save_dir), final_metrics)


if __name__ == "__main__":
	main()