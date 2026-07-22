# Supplied Lexicon Inventory

Inspection date: 2026-07-22

This inventory describes the files currently present under `source_lexicons/`.
The files were read and hashed but not modified. Counts below refer to the
selected primary English source file for each adapter, not translations or
alternate layouts bundled in the packages.

## Summary

| VerseVAD ID | Resource and version | Dimensions/categories | Source scale | Primary entries | Unit represented |
|---|---|---|---|---:|---|
| `warriner_vad_2013` | Warriner et al. affective norms (2013; no package version stated) | valence, arousal, dominance | 1–9 rating scale | 13,915 rows | described as English lemmas; 102 rows contain whitespace |
| `nrc_vad_v1` | NRC VAD Lexicon v1 | valence, arousal, dominance | 0–1 | 19,971 rows | described as English words; 132 rows contain whitespace |
| `nrc_vad_v2_1` | NRC VAD Lexicon v2.1 | valence, arousal, dominance | −1–1 | 54,801 rows | 44,728 unigrams and 10,073 whitespace-containing terms |
| `nrc_emotion_v0_92` | NRC Emotion Lexicon v0.92 | 8 emotions plus positive and negative sentiment | binary 0/1 association | 14,154 terms; 141,540 term-category rows | word-level union of sense annotations |
| `nrc_emotion_intensity_v1` | NRC Emotion Intensity Lexicon v1 | intensity for 8 emotions | 0–1 | 5,891 terms; 9,829 term-emotion rows | word-emotion pairs |

Whitespace counts are structural observations, not final phrase-policy
decisions. Hyphenated forms without whitespace are not included in those
counts.

## 1. Warriner et al. affective norms

- **Authors/publisher:** Amy Beth Warriner, Victor Kuperman, and Marc Brysbaert;
  the local package is a secondary XANEW distribution from JULIE Lab.
- **Version/date:** the package states the 2013 paper but provides no dataset
  version or local acquisition date.
- **Dimensions:** valence, arousal, and dominance, with overall means, standard
  deviations, rating counts, and demographic subsets.
- **Scale:** the ratings use a 1–9 scale. The local README does not itself state
  that scale; it is corroborated by the supplied NRC VAD v2 paper's comparison
  of existing lexicons and should be checked against the original Warriner
  publication before a public release.
- **Primary source file:**
  `source_lexicons/XANEW-master/XANEW-master/Ratings_Warriner_et_al.csv`
- **Documentation file:**
  `source_lexicons/XANEW-master/XANEW-master/README.md`
- **Observed structure:** comma-separated file with a header; 13,915 rows and
  13,915 unique source terms; no blank terms, malformed score rows, duplicate
  source-term keys, or out-of-range overall V/A/D means. Ten pairs collapse to
  the same key under case-insensitive lookup while retaining different source
  capitalization and ratings.
- **License stated by package:** Creative Commons
  Attribution-NonCommercial-NoDerivs 3.0 Unported. This is stated by the
  secondary distributor; an independent original license file is not supplied.
- **Required citation:** Warriner, A. B., Kuperman, V., & Brysbaert, M. (2013).
  “Norms of valence, arousal, and dominance for 13,915 English lemmas.”
  *Behavior Research Methods*, 45, 1191–1207.
- **SHA-256:**
  `78ac8107c78e116bb96538fae4faa47281a155f5f8fe39f30bbc6ea3db05b446`
- **Human review:** confirm original provenance, source version, license text,
  and whether the 102 whitespace-containing terms should use phrase matching.
  Case-colliding ratings must remain separate: exact source capitalization may
  disambiguate them, while unresolved forms should be flagged rather than
  assigned an arbitrary rating.
- **Adapter status:** implemented and contract-tested in Phase 1. All source
  values remain on the 1–9 scale; separate 0–1 values use
  `(original - 1) / 8`. Phrase matching remains deferred.

## 2. NRC VAD Lexicon v1

- **Creator/publisher:** Saif M. Mohammad, National Research Council Canada.
- **Version/date:** version 1, released July 2018; README updated August 2022.
- **Dimensions and scale:** valence, arousal, and dominance on 0–1 scales.
- **Primary source file:**
  `source_lexicons/NRC-VAD-Lexicon/NRC-VAD-Lexicon/NRC-VAD-Lexicon.txt`
- **Documentation:** `README.txt`, `Paper-VAD-ACL2018.pdf`,
  `Paper-Practical-Ethical-Considerations-Lexicons.pdf`, and
  `Paper-Ethics-Sheet-Emotion-Recognition.pdf` in the same package directory.
- **Observed structure:** headerless, four-column tab-separated file; 19,971
  rows and unique terms; no blank terms, malformed rows, duplicate term keys,
  or scores outside 0–1. There are 132 whitespace-containing terms.
- **Terms:** free for non-commercial research and educational purposes;
  attribution and citation required; data redistribution prohibited; commercial
  use requires contacting the author. This is a custom terms-of-use statement,
  not a standard open-source license.
- **Required citation:** Mohammad, S. M. (2018). “Obtaining Reliable Human
  Ratings of Valence, Arousal, and Dominance for 20,000 English Words.”
  *Proceedings of the 56th Annual Meeting of the Association for Computational
  Linguistics*.
- **SHA-256:**
  `fd49023f760155c8377424d96ca18d57c6685891d78ba381e47af6f4a1b148a7`
- **Human review:** determine the phrase policy for the 132 terms containing
  whitespace; do not infer that every row is necessarily a single token.

## 3. NRC VAD Lexicon v2.1

- **Creator/publisher:** Saif M. Mohammad, National Research Council Canada.
- **Version/date:** version 2.1, released March 2025.
- **Dimensions and scale:** valence, arousal, and dominance on −1–1 scales.
- **Primary source file:**
  `source_lexicons/NRC-VAD-Lexicon-v2.1/NRC-VAD-Lexicon-v2.1/NRC-VAD-Lexicon-v2.1.txt`
- **Documentation:** `README.txt`, `Paper-VAD-v2-2025.pdf`,
  `Paper-VAD-ACL2018.pdf`, and the practical/ethical papers in the same package.
- **Observed structure:** header plus four tab-separated columns; 54,801 rows
  and unique terms; no blank terms, malformed rows, duplicate term keys, or
  scores outside −1–1. Exactly 10,073 primary-file terms contain whitespace.
- **Unit:** English unigrams and multiword expressions. The package provides
  separate `Unigrams/` and `MWE/` layouts in addition to the primary file.
- **Terms:** free for non-commercial research and educational purposes;
  attribution and citation required; data redistribution prohibited; commercial
  use requires contacting the author.
- **Required citations:**
  - Mohammad, S. M. (2025). “NRC VAD Lexicon v2: Norms for Valence, Arousal,
    and Dominance for over 55k English Terms.” arXiv:2503.23547.
  - Mohammad, S. M. (2018). “Obtaining Reliable Human Ratings of Valence,
    Arousal, and Dominance for 20,000 English Words.” *ACL 2018*.
- **SHA-256:**
  `42c718817fc91d5c133581b24b0bb31d2b14a0b16edb19bc6ce6ab70343e5a45`
- **Important family note:** v1 and v2.1 are versions of the same NRC VAD
  family, not independent replications. v2 includes entries collected using a
  different rating procedure as documented by the supplied paper and README.

## 4. NRC Emotion Lexicon v0.92

- **Creators/publisher:** Saif M. Mohammad and Peter D. Turney, National
  Research Council Canada.
- **Version/date:** version 0.92, released 10 July 2011; README updated August
  2022.
- **Categories:** anger, anticipation, disgust, fear, joy, sadness, surprise,
  trust, negative, and positive.
- **Scale:** binary association, 0 or 1. Categories are not intensity scores.
- **Primary source file:**
  `source_lexicons/NRC-Emotion-Lexicon/NRC-Emotion-Lexicon/NRC-Emotion-Lexicon-Wordlevel-v0.92.txt`
- **Documentation:** `README.txt`, `Paper1_NRC_Emotion_Lexicon.pdf`,
  `Paper2_NRC_Emotion_Lexicon.pdf`, and the practical/ethical papers in the same
  package.
- **Observed structure:** headerless three-column, tab-separated long format;
  every one of 14,154 unique terms has ten category rows, for 141,540
  term-category rows. No blank terms, malformed rows, duplicate term-category
  keys, or non-binary values were found.
- **Unit:** word-level associations created by taking the union of associations
  across supplied sense annotations. The package also contains a separate
  sense-level file; it is not the selected primary adapter source.
- **Terms:** free for non-commercial research and educational purposes;
  attribution and citation required; data redistribution prohibited; commercial
  use requires contacting the author.
- **Required citations:**
  - Mohammad, S. M., & Turney, P. D. (2013). “Crowdsourcing a Word-Emotion
    Association Lexicon.” *Computational Intelligence*, 29(3), 436–465.
  - Mohammad, S. M., & Turney, P. D. (2010). “Emotions Evoked by Common Words
    and Phrases: Using Mechanical Turk to Create an Emotion Lexicon.”
    *Proceedings of the NAACL-HLT Workshop on Computational Approaches to
    Analysis and Generation of Emotion in Text*, 26–34.
- **SHA-256:**
  `02c661544f4f12ae0c14f9576a10959e8d39a151bb091e455a71a08dcaa2535a`
- **Human review:** none blocking. The word-level union should be described
  clearly in methods reports because it does not disambiguate senses in context.

## 5. NRC Emotion Intensity Lexicon v1

- **Creator/publisher:** Saif M. Mohammad, National Research Council Canada.
- **Version/date:** version 1, released March 2020; README updated August 2022.
- **Categories:** anger, anticipation, disgust, fear, joy, sadness, surprise,
  and trust.
- **Scale:** real-valued emotion intensity from 0 to 1 for each supplied
  word-emotion pair.
- **Primary source file:**
  `source_lexicons/NRC-Emotion-Intensity-Lexicon/NRC-Emotion-Intensity-Lexicon/NRC-Emotion-Intensity-Lexicon-v1.txt`
- **Documentation:** `README.txt`, `Paper-lrec2018-word-emotion.pdf`, and the
  practical/ethical papers in the same package.
- **Observed structure:** headerless three-column tab-separated long format;
  9,829 word-emotion pairs across 5,891 unique terms; no blank terms, malformed
  rows, duplicate word-emotion keys, or scores outside 0–1.
- **Unit:** independently scored word-emotion pairs. Absence of a pair must not
  be converted into an intensity of zero in primary means.
- **Terms:** free for non-commercial research and educational purposes;
  attribution and citation required; data redistribution prohibited; commercial
  use requires contacting the author.
- **Required citation:** Mohammad, S. M. (2018). “Word Affect Intensities.”
  *Proceedings of the 11th Language Resources and Evaluation Conference*.
- **SHA-256:**
  `2bed5450b43134e4f849b013424eb76a76e2bdc0ec35df7ec0a0a477031239cb`
- **Human review:** the supplied research paper describes the earlier
  four-emotion release, while the README and current file cover eight emotions.
  Methods reports must cite the paper and record that the analyzed source is
  the later version 1 package.

## Integrity result

All five primary files passed the Phase 0 structural checks:

- expected primary file present;
- expected columns present where headers exist;
- numeric values parse successfully;
- source-scale range checks pass;
- no blank terms;
- no malformed rows;
- no duplicate source primary keys;
- ten Warriner case-insensitive lookup collisions preserved for explicit
  resolution or review.

This validates file structure, not the scholarly correctness of individual
ratings or the suitability of a particular match in context.

To repeat the read-only check, run `python scripts/inspect_lexicons.py` once the
project runtime is installed.
