"""Poetry-preserving, POS-sensitive linguistic preprocessing."""

from __future__ import annotations

import bisect
import hashlib
from dataclasses import dataclass
from typing import Protocol

from versevad.models import PreprocessingMetadata, TextDocument, TokenRecord
from versevad.normalization import normalize_lookup, strip_edge_punctuation


DEFAULT_RECIPE_ID = "versevad-default-preprocessing-v1"


class PreprocessingError(RuntimeError):
    """A plain-language preprocessing failure with optional technical detail."""

    def __init__(self, message: str, technical_detail: str = "") -> None:
        super().__init__(message)
        self.technical_detail = technical_detail


class TextPreprocessor(Protocol):
    @property
    def metadata(self) -> PreprocessingMetadata: ...

    def process(self, document: TextDocument) -> tuple[TokenRecord, ...]: ...


def create_text_document(text_id: str, title: str, original_text: str) -> TextDocument:
    """Create an immutable text-version identity without changing the text."""

    digest = hashlib.sha256(original_text.encode("utf-8")).hexdigest()
    return TextDocument(
        text_id=text_id,
        title=title,
        original_text=original_text,
        text_sha256=digest,
        text_version_id=f"{text_id}:{digest[:16]}",
    )


@dataclass(frozen=True)
class _LineLocation:
    number: int
    stanza: int
    start: int
    context: str


class _LineIndex:
    def __init__(self, text: str) -> None:
        raw_lines = text.splitlines(keepends=True)
        if not raw_lines:
            raw_lines = [""]
        if raw_lines and sum(len(line) for line in raw_lines) < len(text):
            raw_lines.append(text[sum(len(line) for line in raw_lines) :])

        locations: list[_LineLocation] = []
        starts: list[int] = []
        offset = 0
        stanza = 0
        inside_stanza = False
        for number, raw_line in enumerate(raw_lines, start=1):
            context = raw_line.rstrip("\r\n")
            if context.strip():
                if not inside_stanza:
                    stanza += 1
                inside_stanza = True
            else:
                inside_stanza = False
            starts.append(offset)
            locations.append(
                _LineLocation(
                    number=number,
                    stanza=max(stanza, 1),
                    start=offset,
                    context=context,
                )
            )
            offset += len(raw_line)

        self._starts = starts
        self._locations = locations

    def locate(self, character_offset: int) -> _LineLocation:
        index = max(0, bisect.bisect_right(self._starts, character_offset) - 1)
        return self._locations[index]


class SpacyEnglishPreprocessor:
    """Use a pinned spaCy English pipeline while retaining poem structure."""

    def __init__(self, model_name: str = "en_core_web_sm") -> None:
        try:
            import spacy

            self._nlp = spacy.load(model_name, exclude=["ner"])
        except (ImportError, OSError) as error:
            raise PreprocessingError(
                "VerseVAD could not load its English linguistic model. "
                "No text was changed. Run the project setup again, then retry.",
                technical_detail=str(error),
            ) from error
        self._model_name = model_name

    @property
    def metadata(self) -> PreprocessingMetadata:
        return PreprocessingMetadata(
            recipe_id=DEFAULT_RECIPE_ID,
            pipeline_name=self._model_name,
            pipeline_version=str(self._nlp.meta.get("version", "unknown")),
            disabled_components=("ner",),
        )

    def _merge_possessives(self, document: object) -> None:
        spans = []
        for token in document[:-1]:
            following = document[token.i + 1]
            touching = token.idx + len(token.text) == following.idx
            if (
                touching
                and following.text in {"'s", "’s"}
                and following.pos_ == "PART"
                and token.pos_ in {"NOUN", "PROPN"}
            ):
                spans.append(document[token.i : token.i + 2])
        if not spans:
            return
        with document.retokenize() as retokenizer:
            for span in spans:
                head = span[0]
                retokenizer.merge(
                    span,
                    attrs={
                        "LEMMA": head.lemma_,
                        "POS": head.pos,
                        "TAG": head.tag,
                    },
                )

    def process(self, document: TextDocument) -> tuple[TokenRecord, ...]:
        spacy_document = self._nlp(document.original_text)
        self._merge_possessives(spacy_document)
        line_index = _LineIndex(document.original_text)

        sentence_positions: dict[int, tuple[int, int]] = {}
        try:
            for sentence_number, sentence in enumerate(spacy_document.sents, start=1):
                for position, token in enumerate(sentence, start=1):
                    sentence_positions[token.i] = (sentence_number, position)
        except ValueError:
            sentence_positions = {}

        records: list[TokenRecord] = []
        for token in spacy_document:
            if token.is_space:
                continue
            location = line_index.locate(token.idx)
            token_position = len(records) + 1
            sentence_number, position_in_sentence = sentence_positions.get(
                token.i, (None, None)
            )
            surface = token.text
            stripped = strip_edge_punctuation(surface)
            lemma = token.lemma_ or surface
            warnings: list[str] = []
            if token.pos_ == "X":
                warnings.append("The linguistic model assigned an uncertain POS tag (X).")
            if not token.lemma_:
                warnings.append("The linguistic model did not provide a lemma.")

            records.append(
                TokenRecord(
                    token_id=f"{document.text_version_id}:t{token_position}",
                    text_id=document.text_id,
                    text_version_id=document.text_version_id,
                    section_number=1,
                    stanza_number=location.stanza,
                    line_number=location.number,
                    token_position=token_position,
                    sentence_number=sentence_number,
                    token_position_in_sentence=position_in_sentence,
                    character_start=token.idx,
                    character_end=token.idx + len(token.text),
                    surface_form=surface,
                    lowercase_form=surface.lower(),
                    punctuation_stripped_form=stripped,
                    normalized_form=normalize_lookup(surface),
                    part_of_speech=token.pos_,
                    lemma=lemma,
                    normalized_lemma=normalize_lookup(lemma),
                    morphological_features=str(token.morph),
                    is_punctuation=bool(token.is_punct),
                    is_numeric=bool(token.like_num),
                    is_proper_noun=token.pos_ == "PROPN",
                    is_stopword=bool(token.is_stop),
                    context=location.context,
                    preprocessing_warnings=tuple(warnings),
                )
            )
        return tuple(records)
