"""Transparent, offline BM25-style lexical playbook retrieval with source citations."""
from __future__ import annotations

from collections import Counter
from math import log
import re

from .models import Article, Citation

STOP = frozenset("a an the is are of to and for in on by with from as this that who what where i we our an be or it if at do can need user users employee account ticket help please was were need unable issue".split())
TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return [part for part in TOKEN.findall(text.lower()) if len(part) >= 2 and part not in STOP]


def retrieve(query: str, category: str, articles: list[Article], *, top_k: int = 3) -> list[Citation]:
    """Rank relevant docs without an API, model or embedding download.

    Retrieval score is a *ranking heuristic*, not calibrated probability.
    """
    if top_k <= 0 or not articles:
        return []
    tokens = [tokenize(f"{a.title} {a.body}") for a in articles]
    lengths = [len(x) for x in tokens]
    avg_len = max(1, sum(lengths) / len(lengths))
    query_tokens = Counter(tokenize(query))
    if not query_tokens:
        query_tokens = Counter(tokenize(category))
    document_frequency = Counter(word for seq in tokens for word in set(seq))
    ranked = []
    for article, words, length in zip(articles, tokens, lengths):
        freq = Counter(words)
        score = 0.0
        for term, qfreq in query_tokens.items():
            tf = freq[term]
            if not tf:
                continue
            idf = log(1.0 + (len(articles) - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5))
            score += idf * (tf * 2.2 / (tf + 1.2 * (0.25 + 0.75 * length / avg_len))) * min(qfreq, 2)
        if article.category.lower() == category.lower():
            score += 4.0
        if score > 0:
            snippet = article.body.replace("\n", " ").strip()[:230]
            ranked.append(Citation(article.article_id, article.title, snippet, round(score, 3)))
    return sorted(ranked, key=lambda x: (-x.retrieval_score, x.article_id))[:top_k]
