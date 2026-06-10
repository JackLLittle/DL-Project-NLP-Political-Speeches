
"""PyTorch dataloaders for the cleaned us2020 speech corpus.
"""

from __future__ import annotations

import glob
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset


DEFAULT_BASE_PATH = Path(__file__).resolve().parent / "us2020data" / "data_clean"
DEFAULT_TEXT_COLUMNS = ("CleanText", "RawText")
DEFAULT_TRUMP_LABEL = "Donald Trump"


def _normalize_text(value) -> str:
	if pd.isna(value):
		return ""
	return " ".join(str(value).split())


def _read_speech_file(file_path: Path) -> pd.DataFrame:
	if file_path.suffix == ".jsonl":
		frame = pd.read_json(file_path, lines=True)
	elif file_path.suffix == ".tsv":
		frame = pd.read_csv(file_path, sep="\t")
	elif file_path.suffix == ".csv":
		frame = pd.read_csv(file_path)
	elif file_path.suffix == ".parquet":
		try:
			frame = pd.read_parquet(file_path)
		except Exception as exc:  # pragma: no cover - depends on optional parquet engine
			raise RuntimeError(
				"Reading parquet files requires an installed parquet engine such as pyarrow or fastparquet."
			) from exc
	else:
		raise ValueError(f"Unsupported file type: {file_path}")

	frame = frame.copy()
	frame["__source_file__"] = str(file_path)
	return frame


def _resolve_input_files(
	base_path: Path,
	file_pattern: Optional[str],
	file_format: str,
) -> List[Path]:
	if file_pattern:
		pattern_path = Path(file_pattern)
		if pattern_path.is_absolute():
			pattern = str(pattern_path)
		else:
			pattern = str(base_path / file_pattern)
		files = sorted(Path(path) for path in glob.glob(pattern, recursive=True))
	else:
		pattern = str(base_path / "**" / f"*.{file_format}")
		files = sorted(Path(path) for path in glob.glob(pattern, recursive=True))

	if not files:
		raise FileNotFoundError(
			f"No files found for pattern {pattern!r}. Check base_path={base_path!r} and file_format={file_format!r}."
		)

	return files


def load_speech_dataframe(
	base_path: str | Path = DEFAULT_BASE_PATH,
	file_pattern: Optional[str] = None,
	file_format: str = "jsonl",
	sources: Optional[Sequence[str]] = None,
	candidates: Optional[Sequence[str]] = None,
	text_column: str = "CleanText",
) -> pd.DataFrame:
	"""Load and concatenate cleaned speech records into one DataFrame."""

	base_path = Path(base_path)
	files = _resolve_input_files(base_path, file_pattern, file_format)
	frames = [_read_speech_file(file_path) for file_path in files]
	dataframe = pd.concat(frames, ignore_index=True, sort=False)

	if sources and "Source" in dataframe.columns:
		dataframe = dataframe[dataframe["Source"].isin(list(sources))]

	if candidates and "POTUS" in dataframe.columns:
		dataframe = dataframe[dataframe["POTUS"].isin(list(candidates))]

	if text_column not in dataframe.columns:
		fallback_column = next((column for column in DEFAULT_TEXT_COLUMNS if column in dataframe.columns), None)
		if fallback_column is None:
			raise KeyError(
				f"None of the expected text columns {DEFAULT_TEXT_COLUMNS!r} were found in the dataset."
			)
		text_column = fallback_column

	dataframe = dataframe.copy()
	dataframe[text_column] = dataframe[text_column].map(_normalize_text)
	dataframe = dataframe[dataframe[text_column] != ""]

	if "SpeechID" in dataframe.columns:
		dataframe = dataframe.drop_duplicates(subset=["SpeechID"])

	if "Date" in dataframe.columns:
		dataframe["Date"] = pd.to_datetime(dataframe["Date"], errors="coerce")

	return dataframe.reset_index(drop=True)


def _split_dataframe(
	dataframe: pd.DataFrame,
	label_column: Optional[str],
	split_ratios: Sequence[float],
	seed: int,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
	if len(split_ratios) != 3:
		raise ValueError("split_ratios must contain exactly three values: train, test, and dev.")

	total = float(sum(split_ratios))
	if abs(total - 1.0) > 1e-6:
		raise ValueError("split_ratios must sum to 1.0.")

	train_ratio, test_ratio, dev_ratio = split_ratios

	def split_group(group: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
		shuffled = group.sample(frac=1.0, random_state=seed).reset_index(drop=True)
		size = len(shuffled)
		train_end = int(size * train_ratio)
		test_end = train_end + int(size * test_ratio)
		train_part = shuffled.iloc[:train_end]
		test_part = shuffled.iloc[train_end:test_end]
		dev_part = shuffled.iloc[test_end:]
		return train_part, test_part, dev_part

	if label_column and label_column in dataframe.columns:
		train_frames: List[pd.DataFrame] = []
		test_frames: List[pd.DataFrame] = []
		dev_frames: List[pd.DataFrame] = []
		for _, group in dataframe.groupby(label_column, dropna=False):
			train_part, test_part, dev_part = split_group(group)
			train_frames.append(train_part)
			test_frames.append(test_part)
			dev_frames.append(dev_part)

		train_df = pd.concat(train_frames, ignore_index=True).sample(frac=1.0, random_state=seed).reset_index(drop=True)
		test_df = pd.concat(test_frames, ignore_index=True).sample(frac=1.0, random_state=seed).reset_index(drop=True)
		dev_df = pd.concat(dev_frames, ignore_index=True).sample(frac=1.0, random_state=seed).reset_index(drop=True)
		return train_df, test_df, dev_df

	shuffled = dataframe.sample(frac=1.0, random_state=seed).reset_index(drop=True)
	size = len(shuffled)
	train_end = int(size * train_ratio)
	test_end = train_end + int(size * test_ratio)
	return (
		shuffled.iloc[:train_end].reset_index(drop=True),
		shuffled.iloc[train_end:test_end].reset_index(drop=True),
		shuffled.iloc[test_end:].reset_index(drop=True),
	)


class SpeechCorpusDataset(Dataset):
	"""Dataset for cleaned speech transcripts.

	By default each item is returned as ``(text, label)``. If
	``return_metadata`` is set, the sample becomes ``(text, label, metadata)``
	where ``metadata`` contains all remaining columns from the source row.
	"""

	def __init__(
		self,
		dataframe: pd.DataFrame,
		text_column: str = "CleanText",
		label_column: Optional[str] = "POTUS",
		positive_label: Optional[str] = DEFAULT_TRUMP_LABEL,
		return_metadata: bool = False,
	):
		if text_column not in dataframe.columns:
			raise KeyError(f"text_column {text_column!r} is not present in the dataframe.")

		self.dataframe = dataframe.reset_index(drop=True).copy()
		self.text_column = text_column
		self.label_column = label_column if label_column in self.dataframe.columns else None
		self.positive_label = positive_label
		self.return_metadata = return_metadata

	def __len__(self) -> int:
		return len(self.dataframe)

	def __getitem__(self, index: int):
		row = self.dataframe.iloc[index]
		text = row[self.text_column]

		if self.label_column is not None:
			raw_label = row[self.label_column]
			if self.positive_label is None:
				label = raw_label
			else:
				label = int(raw_label == self.positive_label)
		else:
			label = None

		if not self.return_metadata:
			if self.label_column is None:
				return text
			return text, label

		metadata = row.drop(labels=[self.text_column], errors="ignore")
		if self.label_column is not None and self.label_column in metadata.index:
			metadata = metadata.drop(labels=[self.label_column])
		return text, label, metadata.to_dict()


def get_data_loaders(
	base_path: str = DEFAULT_BASE_PATH,
	batch_size: int = 32,
	text_column: str = "CleanText",
	label_column: str = "POTUS",
		positive_label: Optional[str] = DEFAULT_TRUMP_LABEL,
	sources: Optional[Sequence[str]] = None,
	candidates: Optional[Sequence[str]] = None,
	file_pattern: Optional[str] = None,
	file_format: str = "jsonl",
	split_ratios: Sequence[float] = (0.8, 0.1, 0.1),
	seed: int = 42,
	num_workers: int = 0,
	return_metadata: bool = False,
	shuffle_train: bool = True,
):
	"""Create train / test / dev dataloaders for the cleaned speech corpus."""

	dataframe = load_speech_dataframe(
		base_path=base_path,
		file_pattern=file_pattern,
		file_format=file_format,
		sources=sources,
		candidates=candidates,
		text_column=text_column,
	)

	train_df, test_df, dev_df = _split_dataframe(dataframe, label_column, split_ratios, seed)

	train_dataset = SpeechCorpusDataset(
		train_df,
		text_column=text_column if text_column in train_df.columns else next(
			(column for column in DEFAULT_TEXT_COLUMNS if column in train_df.columns), text_column
		),
		label_column=label_column,
		positive_label=positive_label,
		return_metadata=return_metadata,
	)
	test_dataset = SpeechCorpusDataset(
		test_df,
		text_column=text_column if text_column in test_df.columns else next(
			(column for column in DEFAULT_TEXT_COLUMNS if column in test_df.columns), text_column
		),
		label_column=label_column,
		positive_label=positive_label,
		return_metadata=return_metadata,
	)
	dev_dataset = SpeechCorpusDataset(
		dev_df,
		text_column=text_column if text_column in dev_df.columns else next(
			(column for column in DEFAULT_TEXT_COLUMNS if column in dev_df.columns), text_column
		),
		label_column=label_column,
		positive_label=positive_label,
		return_metadata=return_metadata,
	)

	train_loader = DataLoader(
		train_dataset,
		batch_size=batch_size,
		shuffle=shuffle_train,
		num_workers=num_workers,
	)
	test_loader = DataLoader(
		test_dataset,
		batch_size=batch_size,
		shuffle=False,
		num_workers=num_workers,
	)
	dev_loader = DataLoader(
		dev_dataset,
		batch_size=batch_size,
		shuffle=False,
		num_workers=num_workers,
	)

	return train_loader, test_loader, dev_loader


if __name__ == "__main__":
	train_loader, test_loader, dev_loader = get_data_loaders()
	batch = next(iter(train_loader))
	print(type(batch))
