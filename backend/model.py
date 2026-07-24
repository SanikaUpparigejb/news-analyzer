import torch
from transformers import (
    BartForConditionalGeneration,
    BartTokenizer,
    pipeline
)

print("Loading summarization model (DistilBART-XSum)...")
# Switched from facebook/bart-large-cnn to sshleifer/distilbart-xsum-12-6.
#
# Why: bart-large-cnn was fine-tuned on CNN/DailyMail, whose reference
# summaries are themselves highly extractive (they reuse large spans of
# the source article almost verbatim) — the model inherits that bias.
# XSum-trained models are fine-tuned on BBC single-sentence summaries,
# which forces genuine compression/paraphrasing rather than span copying.
# The "distil" variant is also roughly 2x faster on CPU since it has fewer
# decoder layers, which directly addresses slow response times.
#
# Tradeoff: XSum-style summaries are naturally shorter and more compressed
# than CNN-style ones, and can occasionally drop minor details in service
# of brevity — that's the cost of being more abstractive.
bart_tokenizer = BartTokenizer.from_pretrained("sshleifer/distilbart-xsum-12-6")
bart_model     = BartForConditionalGeneration.from_pretrained("sshleifer/distilbart-xsum-12-6")
bart_model.eval()  # inference mode — disables dropout

print("Loading classification model...")
classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli"
)

print("Loading sentiment model...")
sentiment_analyzer = pipeline(
    "text-classification",          # "sentiment-analysis" alias removed in 5.x
    model="distilbert-base-uncased-finetuned-sst-2-english"
)

print("All models loaded.")

TOPICS = [
    "politics", "technology", "sports",
    "business", "health", "science",
    "entertainment", "environment"
]


def summarize(text: str) -> str:
    # IMPORTANT: truncate by tokens, not words. BART uses subword tokenization,
    # so word count is not a reliable proxy for token count — a sentence with
    # 500 words can easily produce 650+ tokens depending on vocabulary.
    # truncation=True + max_length here lets the tokenizer itself handle this
    # correctly instead of us guessing a word-count cutoff.
    inputs = bart_tokenizer(
        text,
        return_tensors="pt",
        max_length=1024,
        truncation=True
    )

    with torch.no_grad():  # saves memory during inference
        summary_ids = bart_model.generate(
            inputs["input_ids"],
            # XSum-style models naturally produce shorter, denser summaries
            # than CNN-style ones. Widened the range slightly from typical
            # CNN-tuned defaults (50-150) so output isn't too terse.
            max_length=120,
            min_length=30,
            length_penalty=2.0,
            num_beams=4,
            early_stopping=True
        )

    return bart_tokenizer.decode(summary_ids[0], skip_special_tokens=True)


def classify_topic(text: str) -> dict:
    # bart-large-mnli has a max sequence length of 512 tokens.
    # ZeroShotClassificationPipeline truncates by default internally
    # (TruncationStrategy.ONLY_FIRST), but it does NOT accept a max_length
    # kwarg through preprocess() — passing one would either error or be
    # silently ignored. We rely on its built-in truncation instead, and
    # never pre-truncate by word count (that's what caused the original
    # "tensor size 573 vs 512" mismatch — word count is not token count).
    result = classifier(text, TOPICS)

    top = sorted(
        zip(result["labels"], result["scores"]),
        key=lambda x: x[1],
        reverse=True
    )[:3]

    return {
        "top_topic":  top[0][0],
        "confidence": round(top[0][1] * 100, 1),
        "all_scores": {label: round(score * 100, 1) for label, score in top}
    }


def analyze_sentiment(text: str) -> dict:
    # distilbert-sst2 caps at 512 tokens. TextClassificationPipeline.preprocess
    # forwards **tokenizer_kwargs directly to the tokenizer, so truncation
    # and max_length here are valid and actually applied.
    result = sentiment_analyzer(
        text,
        truncation=True,
        max_length=512
    )[0]

    mapping = {"POSITIVE": "Positive 😊", "NEGATIVE": "Negative 😟"}
    return {
        "sentiment":  mapping.get(result["label"], result["label"]),
        "confidence": round(result["score"] * 100, 1)
    }