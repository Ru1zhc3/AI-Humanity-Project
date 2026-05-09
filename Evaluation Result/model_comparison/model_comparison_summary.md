# Model Comparison Analysis for Results Slides

This analysis compares `Codex gpt-5.4-mini` and `Gemma 4` on political-lean labels across languages and perturbations.

## Presentation-Ready Takeaways

1. **Language changes political-lean judgments even without perturbation.** Codex keeps the same lean across all translated versions for `53.8%` of source statements; Gemma 4 keeps the same lean for `25.3%`.
2. **Perturbation changes political-lean judgments more strongly than translation alone.** Codex stability across all 14 perturbations averages `13.6%`; Gemma 4 averages `6.3%`.
3. **Model identity matters.** Codex and Gemma 4 agree on `64.6%` of no-perturbation language rows and `59.5%` of perturbation rows.
4. **The lowest model agreement under perturbation appears in:** Presupposition Loading (45.6%), Colloquial (51.1%), Loss Framing (56.2%).
5. **The lowest model agreement without perturbation appears in:** Amharic (54.7%), Simplified Mandarin (57.8%), Farsi (59.6%).

## How This Connects To The Proposal

The proposal asks whether political-content moderation/evaluation changes across languages, model families, and prompt framing. These results support that framing:

- The same source statement can move across political-compass labels after translation.
- Perturbations are not merely surface rewrites; they change model political-lean judgments.
- Differences appear both within one model and between models, which suggests the behavior is not just a translation artifact.

## Recommended Slide Placement

- **Slide 20 / Shifted Lean:** insert `figures/final_model_language_lean_heatmap.svg` to show no-perturbation language effects by model.
- **Slide 25 / Outcomes:** insert `figures/model_stability_agreement.svg` or `figures/presentation_core_results_table.svg` as the main evidence chart/table.
- **Slide 26 / Conclusion:** use the conclusion text below and optionally add `figures/perturbation_model_agreement.svg` if there is room.

## Suggested Result / Outcome Wording

**Result:** Across the original, non-perturbed statements, political-lean labels vary by language and by model. This means translation alone can change how a model places the same political claim on the political compass.

**Outcome 1:** Language is an evaluation variable. Even when statements are semantically equivalent, both models recode some translations into different political-lean categories.

**Outcome 2:** Perturbation amplifies instability. Prompt variants such as open-ended, loss-framed, and hedged wording create larger political-lean shifts and lower cross-model agreement.

**Conclusion:** Political-content moderation is shaped by both language and prompt form. Because Codex and Gemma 4 disagree on a substantial share of rows, multilingual moderation should not assume that one model, one language, or one prompt framing gives a neutral baseline.

## Generated Figures

- `figures/model_stability_agreement.svg`
- `figures/final_model_language_lean_heatmap.svg`
- `figures/perturbation_model_language_lean_heatmap.svg`
- `figures/perturbation_model_agreement.svg`
- `figures/presentation_core_results_table.svg`

## Generated Tables

- `tables/presentation_metric_summary.csv`
- `tables/final_language_summary_by_model.csv`
- `tables/final_lean_distribution_model_language_pct.csv`
- `tables/final_cross_model_agreement_by_language.csv`
- `tables/perturbation_language_summary_by_model.csv`
- `tables/perturbation_lean_distribution_model_language_pct.csv`
- `tables/perturbation_cross_model_agreement_by_type.csv`
- `tables/perturbation_stability_by_model_language.csv`
- `tables/perturbation_summary_by_model_type.csv`

## Proposal Lines Used As Context

- Implicit Alignment: Political Content Moderation Across Different Models and Languages
- We want to compare how different models respond when posed with the same political questions but in different languages. The languages we want to test are English, Spanish, and Vietnamese. We will ask 5-6 moderate questions regarding global political topics and measure framing differences, hedging differences, refusal differences, etc as indicators of AI alignment, cultural power and language dominance, and inequities in NLP.
- We will produce a set of rich results showing the existence or lack thereof of certain covert political biases found across different large language models when presented political questions in different languages. We hope to aggregate results for variations in both language and model type. This would provide value to people using large language models in industry for fields like journalism (editorial pieces on political topics, for example). Additionally, it may reveal the areas in which AI needs to become more unbiased, which could in turn allow AI to slowly become better at bias detection in news articles or other opinionated pieces.
- Useful: Our findings may present a potential underlying bias in the model toward the minority. It is important that users are informed of potential model biases, especially covert ones, so they can better interpret model responses.
- Relevant: Our project will fully satisfy the requirement of being relevant. These LLMs present themselves as global tools for education, providing neutral/objective information. It is relevant to assess whether or not a global tool can equitably serve a global community. Implicit political biases may impact fairness of neutrality and safety measures, accessibility to trustworthy information, and the direction of political discourse across cultures.
- Technically interesting: As computer scientists, we have a better understanding of how AI is trained in terms of data, safety protocols, and alignments. This understanding makes us more suited in analyzing AI responses.
- How (and why) did you pick these three languages? Makes sense to include English, but I would think there would be more of interest to learn from Farsi, Chinese (and maybe Mandarin vs. Taiwanese), Arabic, Hebrew, Russian, Ukrainian, Navajo, Klingon, etc. If you can trust machine translation (which I think you can, although does raise its own issues for any language which we don't have direct understanding of), I think you can expand the set of languages and it will lead to more interesting results. 3. I think you should be careful of framing this as "biases" - bias assumes there is some correct ground truth answer to these questions that is uninfluenced by political factors, which I doubt will be true for any of your questions (although you could and probably should include some where there is a clear "correct" answer). (e.g., I thought this one was funny and maybe revealing: https://poe.com/s/hMk7gmOvz2VgB3Yr8v6d vs. https://poe.com/s/C4nTsxHZdil3u2KyJ7zJ).
- Updated list of languages (cover geographical regions):
- Identify datasets (these are good for varying political ideology)
- https://huggingface.co/datasets/promptfoo/political-questions
- https://huggingface.co/datasets/cajcodes/political-bias
- Geo-political and foreign policy
