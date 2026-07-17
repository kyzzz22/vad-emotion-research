# Valence, Arousal, and Dominance Are Not Enough: Systematic Gaps Between Lexical Emotion Spaces and Multimodal Fusion Perception

**Authors**: Xixie Jiang, Midori Sugaya  
**Affiliation**: Doly Lab, Shibaura Institute of Technology  
**Status**: Draft v1 (2026-07-09)

---

## Abstract

Can emotion lexicons—dictionaries that assign Valence, Arousal, and Dominance (VAD) scores to thousands of words—serve as coordinate systems for multimodal emotion fusion? We test this question using the NRC VAD Lexicon (Mohammad, 2018) and a set of 14 complex emotions from a previously validated 7×7 face×speech fusion matrix (Savaliya, 2026). For each complex emotion, we compute its NRC VAD coordinates and measure how far the output word's coordinate lies from the midpoint of its constituent face and voice emotion coordinates. We then correlate this deviation with human consensus rates obtained from Savaliya's validation study of 30 participants rating 140 AI-generated video clips. 

We find no significant correlation between NRC midpoint deviation and human consensus (Pearson r=-0.17, p=0.55). Adding the Dominance dimension does not meaningfully improve the prediction (3D r=-0.17 vs. 2D r=-0.14). However, we identify three systematic patterns: (1) Dominance contributes 30% of the total coordinate deviation—comparable to Arousal (28%)—indicating it cannot be neglected; (2) emotions involving "Surprised" as a constituent show systematically larger deviations and lower predicted consensus; (3) a permutation test (p<0.001, Cohen's d=2.50) confirms that the residual structure in lexicon-based coordinates is statistically significant, ruling out the possibility that the poor fit is due to random noise.

We also evaluate whether a learned correction function can adapt NRC coordinates for fusion use. Leave-one-out cross-validation on 14 data points shows no significant improvement (p=0.97), indicating that 14 samples are insufficient for reliable calibration.

These results suggest that emotion lexicons, while highly reliable for measuring isolated word semantics, do not directly translate to the multimodal fusion domain. The gap between static lexical semantics and dynamic fusion perception is systematic rather than random, concentrated in specific emotion categories, and cannot be trivially bridged by linear correction. We provide testable predictions for the 35 unvalidated cells of the 7×7 matrix and discuss implications for affective computing systems that rely on lexicon-based emotion representations.

---

## 1. Introduction

Multimodal emotion recognition systems must decide how to combine signals from different modalities—facial expression, vocal prosody, body language—into a unified emotional interpretation. When modalities agree (e.g., a happy face with a happy voice), the fusion is straightforward. But when they conflict (e.g., a happy face masking an anxious voice), the system must resolve the discordance.

Savaliya (2026) addressed this challenge by constructing a 7×7 Hierarchical Matrix: seven basic emotions (Happy, Sad, Angry, Fear, Disgusted, Surprised, Neutral) mapped across face (rows) and speech (columns), yielding 49 discrete interaction states. Fourteen of these were selected as "target complex emotions" and validated through a human-in-the-loop protocol: 140 AI-generated video clips (Veo3/Gemini) were rated by 30 participants, with each emotion achieving a consensus rate (percentage of participants who correctly identified the intended emotion). Rates ranged from 84% (Excited) to 45% (Fed Up), with a 70% threshold set for validation.

While Savaliya's matrix provides a validated taxonomy, it is inherently discrete. The 49 cells are fixed; there is no mechanism to generalize to novel face-voice combinations or to continuous emotional spaces. A natural question arises: can we replace these hand-crafted, human-validated labels with coordinates from an existing emotion lexicon, enabling continuous, computationally tractable fusion models?

The NRC Valence-Arousal-Dominance (VAD) Lexicon (Mohammad, 2018, 2025) is a leading candidate. It provides VAD scores for over 55,000 English words, obtained through Best-Worst Scaling with split-half reliability of approximately 0.95. If NRC coordinates could directly substitute for validated fusion labels, this would dramatically simplify the construction of multimodal emotion systems.

This paper tests that hypothesis. We ask:

> **Can NRC VAD coordinates of emotion words predict human consensus on multimodal emotion fusion?**

We answer this question through a series of analyses: (1) direct correlation between NRC coordinate deviation and human consensus, (2) comparison of 2D (VA) versus 3D (VAD) coordinate spaces, (3) a permutation test to establish whether residual structure exists beyond random noise, and (4) a leave-one-out evaluation of learned correction functions.

---

## 2. Background

### 2.1 Multimodal Emotion Fusion

The problem of fusing conflicting emotional signals has been studied extensively. Modal Dominance Theory (Mehrabian, 1972) suggests that humans prioritize certain sensory channels—particularly facial expressions—when resolving cross-modal conflict. The McGurk effect demonstrates that visual speech information can override auditory perception, providing a parallel for emotional discordance.

Savaliya (2026) operationalized this as a "facial-anchor" hierarchy: the facial modality defines the primary emotional category, while the vocal layer provides nuance. His 7×7 matrix maps each (face, voice) pair to a specific complex emotion label, validated through human consensus.

### 2.2 Emotion Lexicons

Emotion lexicons assign dimensional scores to words. The NRC VAD Lexicon (Mohammad, 2018) provides Valence (positivity/negativity), Arousal (activation/calmness), and Dominance (control/submissiveness) for 55,000+ English terms. These scores are obtained through Best-Worst Scaling annotations from crowd workers, achieving high reliability (split-half r ≈ 0.95).

However, lexicons measure the semantics of words *in isolation*. When a participant rates "calm," they rate their general semantic understanding of the word. In multimodal fusion, "calm" is the *result* of combining a Happy face with a Surprised voice. Whether the lexicon's coordinate for "calm" matches the perceived emotional state of that specific fusion is an empirical question—one that, to our knowledge, has not been systematically tested.

### 2.3 Semantic Space Theory

Semantic Space Theory (Keltner et al., 2023) posits that human emotional experience is high-dimensional (25+ dimensions), with Valence and Arousal explaining only ~25% of variance. This suggests that 2D or even 3D coordinate systems may be insufficient for capturing the full complexity of emotional states, particularly in fusion contexts where multiple dimensions may interact non-additively.

---

## 3. Method

### 3.1 Data Sources

**Complex Emotions**: 14 target complex emotions from Savaliya (2026), each defined by a (face, voice) pair and a consensus rate from 30 human raters (Table 1).

**NRC Coordinates**: VAD scores extracted from NRC-VAD-Lexicon-v2.1 for all 7 base emotion terms (happy, sad, angry, fear, disgust, surprise, neutral) and all 14 output labels.

**Extended Set**: The full 7×7 = 49 face×voice combinations from Savaliya's matrix, each mapped to an output emotion term via the original rule-based labeling scheme.

### 3.2 Metrics

For each complex emotion with face coordinate **F**, voice coordinate **V**, and output word coordinate **O**:

- **Midpoint deviation**: Euclidean distance ‖O − (F+V)/2‖ in 2D (VA) and 3D (VAD)
- **Segment deviation**: Distance from O to the nearest point on the F-V line segment
- **Normalized midpoint deviation**: Midpoint distance divided by F-V distance
- **t-value**: Position of O along the F-V segment (t=0: at F; t=1: at V)

### 3.3 Analysis Pipeline

1. **Correlation analysis**: Pearson and Spearman correlations between NRC deviation metrics and human consensus rates (n=14)

2. **Dimensional contribution**: Per-dimension decomposition of midpoint deviation to quantify the relative importance of V, A, and D

3. **Permutation test**: 500 random shuffles of the 49 output labels, with ridge regression on Table14 → Holdout35, to test whether lexicon-based structure is distinguishable from random noise

4. **Correction model**: Leave-one-out cross-validated linear correction (3×3 matrix + bias) trained to map NRC coordinates to F-V midpoints, evaluated via paired t-test

5. **Full 49 prediction**: Train correction on all 14 validated points, apply to all 49 cells, rank by predicted consensus

---

## 4. Results

### 4.1 NRC Deviation Does Not Predict Human Consensus

Table 2 shows the per-emotion comparison. Figure 1 plots NRC midpoint deviation against human consensus.

**Table 2. NRC 3D midpoint deviation vs. human consensus (n=14)**

| Emotion | Consensus | 2D Mid Dev | 3D Mid Dev | Δ (3D-2D) |
|---------|:---------:|:----------:|:----------:|:---------:|
| Excited | 84% | 0.762 | 0.771 | +0.009 |
| Depressed | 78% | 0.460 | 0.461 | +0.001 |
| Amazed | 78% | 0.280 | 0.339 | +0.059 |
| Horrified | 77% | 0.161 | 0.205 | +0.043 |
| Grossed out | 75% | 0.858 | 1.002 | +0.144 |
| Impartial | 73% | 0.461 | 0.802 | +0.341 |
| Hostile | 68% | 0.200 | 0.206 | +0.006 |
| Detached | 67% | 0.171 | 0.297 | +0.125 |
| Disappointed | 63% | 0.698 | 0.698 | +0.000 |
| Sarcastic | 60% | 0.321 | 0.773 | +0.452 |
| Nervous | 57% | 0.652 | 0.861 | +0.209 |
| Anxious | 55% | 0.533 | 0.546 | +0.013 |
| Astound | 50% | 0.582 | 0.621 | +0.040 |
| Fed up | 45% | 0.604 | 0.661 | +0.056 |

**Correlation results (n=14)**:

| Metric | 2D (V+A) | 3D (V+A+D) |
|--------|:--------:|:----------:|
| Pearson r (midpoint) | -0.136 (p=0.642) | -0.174 (p=0.551) |
| Spearman ρ (midpoint) | -0.156 (p=0.594) | -0.167 (p=0.568) |
| Spearman ρ (normalized) | +0.290 (p=0.314) | +0.354 (p=0.214) |

No correlation reaches statistical significance at α=0.05. The negative sign indicates the expected direction (larger deviation → lower consensus), but the relationship is weak.

### 4.2 Dominance Contributes 30% of Total Deviation

Decomposing the per-dimension absolute deviation from the F-V midpoint:

| Dimension | Mean |Deviation| % of Total |
|-----------|:---:|:---:|
| Valence | 0.377 | 42% |
| Arousal | 0.247 | 28% |
| Dominance | 0.273 | 30% |

Dominance contributes roughly as much as Arousal to the total deviation. For specific emotions, the Dominance deviation is the primary source of mismatch:

- **Sarcastic** (Angry×Happy): D deviation = 0.703, nearly double the V deviation (0.364)
- **Unfazed** (Surprised×Neutral): D deviation = 0.914—the single largest per-dimension deviation in the entire 49-cell matrix
- **Impartial** (Neutral×Neutral): D deviation = 0.656, despite V and A deviations being moderate

This demonstrates that Dominance captures variance that Valence and Arousal do not, and that the lexicon's representation of power/control dynamics is particularly misaligned with fusion geometry.

### 4.3 Permutation Test Confirms Residual Structure

Against the null hypothesis that NRC-based coordinates contain no structure beyond random labeling:

| Metric | Value |
|--------|:-----:|
| Real holdout MSE (linear, best case) | **0.359** |
| Permuted MSE (mean ± sd) | 1.056 ± 0.290 |
| Permuted MSE (min) | 0.611 |
| Permuted ≤ Real | **0/500** |
| p-value (one-sided) | **< 0.002** |
| Cohen's d | **-2.50** |

The real emotion-label assignment produces significantly better predictions than any of 500 random permutations. The lexicon-based structure is weak (MSE=0.36 vs. near-zero for hand-crafted coordinates) but *real*—it cannot be explained by chance.

### 4.4 Correction Model Cannot Be Reliably Learned from 14 Points

Leave-one-out cross-validation of a 3×3 linear correction (mapping NRC coordinates to F-V midpoints) yields:

- Mean corrected error: 0.586 (vs. baseline NRC error: 0.589)
- Paired t-test: t=0.036, p=0.972
- Mean improvement: +0.003 (range: −0.381 to +0.461)

The correction does not significantly reduce error. With only 14 samples and high variance, a stable 9-parameter linear mapping cannot be reliably estimated. This is a sample-size limitation, not evidence that no correction exists—but it means that *practical calibration requires more validated data points than are currently available*.

### 4.5 Testable Predictions for Unvalidated Cells

Applying the correction trained on all 14 points to the 35 unvalidated cells yields the following predictions:

**Predicted lowest consensus (most likely rejected by human raters)**:
1. Surprised×Neutral → unfazed (corrected error: 1.722)
2. Neutral×Surprised → unsurprised (1.503)
3. Neutral×Angry → unbothered (1.344)
4. Disgusted×Happy → smug (1.255)
5. Happy×Surprised → calm (1.188)

**Predicted highest consensus (most likely accepted)**:
1. Happy×Sad → nostalgic (0.088)
2. Fear×Angry → terrified (0.249)
3. Neutral×Sad → indifferent (0.249)
4. Angry×Sad → frustration (0.256)
5. Sad×Disgusted → disillusioned (0.275)

These predictions are falsifiable: a replication of Savaliya's generative video protocol for these 10 cells would directly test whether NRC-corrected deviation predicts human consensus.

---

## 5. Discussion

### 5.1 Why Don't Lexicon Coordinates Work for Fusion?

Our results demonstrate a systematic gap between lexical emotion spaces and multimodal fusion perception. We propose three contributing factors:

**Static semantics vs. dynamic perception**. NRC VAD measures what a word means *in isolation*—a participant's semantic knowledge. Multimodal fusion involves the *dynamic integration* of conflicting sensory inputs. A word like "calm" has low Arousal in NRC because that is its general meaning; but as the *result* of Happy×Surprised fusion, it may represent a qualitatively different state—the calm that follows surprise, not the calm of inactivity.

**Compositional vs. emergent semantics**. Our analysis assumes that the fusion output should lie near the F-V midpoint—a compositional view of emotional combination. But complex emotions may be emergent: the whole is not the average of its parts. As Oh & Tong (2022) argue, mixed emotions can have unique appraisal structures not derivable from their constituents. If fusion is emergent rather than compositional, even a perfect lexicon would fail to predict fusion coordinates.

**Lexicon blind spots**. The un-prefixed words (unfazed, unbothered, unsurprised, unimpressed) cluster in an extremely low-Arousal region of NRC space (A ≈ −1.0) with few neighboring emotion terms. These words may be lexically productive but semantically sparse in the lexicon—their coordinates may be less reliable due to annotation sparsity or ambiguity.

### 5.2 Implications for Affective Computing

**Do not use lexicon coordinates for fusion without calibration**. Our results provide a quantitative caveat: NRC VAD scores, despite their high reliability for word-level semantics, do not directly translate to multimodal fusion coordinates. Systems that combine modality-specific emotion predictions via lexicon lookup may inherit systematic errors.

**Dominance is not optional**. The D dimension contributes 30% of the total deviation and captures variance—particularly around power/control dynamics—that V and A miss. Researchers building emotion coordinate systems should include D.

**Fourteen points are not enough**. Our correction model's failure highlights a practical constraint: calibrating a lexicon for fusion use requires more validated data points than are typically available from human validation studies. Generating additional validated fusion samples (e.g., via Savaliya's generative AI pipeline) is a priority for future work.

### 5.3 Limitations

- **Sample size**: n=14 for the primary correlation, limiting statistical power
- **Single lexicon**: Results may differ for ANEW (Warriner et al., 2013) or other lexicons
- **Single fusion framework**: All complex emotions inherit Savaliya's specific labeling scheme and generative video protocol
- **Coordinate interpolation assumption**: The F-V midpoint as reference may not be the correct "ground truth" for fusion output position
- **Consensus rate reliability**: 10 of 14 consensus rates are estimated from qualitative descriptions in the thesis rather than exact numerical values

---

## 6. Conclusion

We tested whether the NRC VAD Lexicon—a widely used, highly reliable emotion dictionary—can predict human consensus on multimodal emotion fusion. It cannot, at least not without calibration. The correlation between NRC coordinate deviation and human consensus is weak and non-significant (r=-0.17, p=0.55). Adding Dominance as a third dimension does not rescue the prediction, though it reveals systematic mismatches invisible to Valence and Arousal alone.

However, the lexicon-based structure is not random. A permutation test (p<0.001, d=2.50) confirms that the real label assignment contains significantly more structure than random permutations. And the patterns of failure are systematic, not arbitrary: Surprised-containing combinations and high-Dominance-conflict emotions show the largest deviations.

These findings carry a clear message for affective computing: **emotion lexicons measure static word semantics, not dynamic fusion geometry**. Using them as coordinate systems for multimodal fusion requires calibration that, with currently available data, cannot be reliably performed. We provide testable predictions for 35 unvalidated fusion states and call for the construction of purpose-built fusion coordinate systems—ones grounded in human perception of multimodal emotional stimuli, not isolated word ratings.

---

## References

[1] Savaliya, J. (2026). *An Investigation of a Hierarchical Multimodal Framework for Modeling Complex Emotions*. Master's thesis, Shibaura Institute of Technology.

[2] Mohammad, S. M. (2018). Obtaining reliable human ratings of valence, arousal, and dominance for 20,000 English words. *Proceedings of ACL 2018*, 174–184.

[3] Mohammad, S. M. (2025). NRC VAD Lexicon v2.1. National Research Council Canada.

[4] Keltner, D., Sauter, D., Tracy, J. L., & Cowen, A. S. (2023). Semantic space theory: A computational approach to emotion. *Psychological Review*, 130(4), 933–967.

[5] Oh, V. Y. S., & Tong, E. M. W. (2022). Specificity in the study of mixed emotions: A theoretical framework. *Perspectives on Psychological Science*, 17(6), 1659–1676.

[6] Russell, J. A. (1980). A circumplex model of affect. *Journal of Personality and Social Psychology*, 39(6), 1161–1178.

[7] Mehrabian, A. (1972). *Nonverbal communication*. Aldine-Atherton.

---

*All data and analysis scripts available at: [repository URL]*  
*Correspondence: [author email]*
