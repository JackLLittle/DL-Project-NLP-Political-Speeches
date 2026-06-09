"""RoBERTa model for binary speech classification.

This module provides a lightweight Hugging Face RoBERTa encoder with a
custom classification head for predicting whether a speech was delivered by
Trump (label 1) or not Trump (label 0).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import torch
from torch import nn
from transformers import AutoTokenizer, RobertaModel


@dataclass
class SpeechClassifierOutput:
    """Simple output container for training and inference."""

    loss: Optional[torch.Tensor]
    logits: torch.Tensor


def build_tokenizer(model_name: str = "roberta-base"):
    """Create the tokenizer paired with the RoBERTa backbone."""

    return AutoTokenizer.from_pretrained(model_name, use_fast=True)


class RobertaTrumpClassifier(nn.Module):
    """Binary classifier that fine-tunes RoBERTa on speech text.

    Parameters
    ----------
    model_name:
        Hugging Face model identifier to load.
    dropout:
        Dropout applied before the classification head.
    freeze_encoder:
        If True, only the classification head is trained.
    """

    def __init__(
        self,
        model_name: str = "roberta-base",
        dropout: float = 0.1,
        freeze_encoder: bool = False,
    ):
        super().__init__()
        self.encoder = RobertaModel.from_pretrained(model_name, add_pooling_layer=False)
        hidden_size = self.encoder.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden_size, 2)

        if freeze_encoder:
            for parameter in self.encoder.parameters():
                parameter.requires_grad = False

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
    ) -> SpeechClassifierOutput:
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)

        pooled_output = outputs.last_hidden_state[:, 0]

        logits = self.classifier(self.dropout(pooled_output))

        loss = None
        if labels is not None:
            loss = nn.CrossEntropyLoss()(logits, labels.long())

        return SpeechClassifierOutput(loss=loss, logits=logits)

    def predict_proba(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Return class probabilities for the two labels."""

        self.eval()
        with torch.no_grad():
            logits = self.forward(input_ids=input_ids, attention_mask=attention_mask).logits
            return torch.softmax(logits, dim=-1)