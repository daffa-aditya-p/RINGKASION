#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
══════════════════════════════════════════════════════════════════════════════════
RINGKASION v2.0.0 - INDONESIAN TEXT SUMMARIZATION ENGINE
══════════════════════════════════════════════════════════════════════════════════

Advanced Indonesian text summarization with state-of-the-art techniques:
1. Nazief-Adriani Indonesian Stemmer - Morphological normalization
2. BM25 Similarity - Proven information retrieval weighting
3. TextRank Algorithm - Graph-based ranking with meaningful similarity
4. Multi-Feature Scoring - Position, length, lexical density, importance signals
5. Lexical Chain Analysis - Discourse-level concept tracking
6. Coverage-Based Selection - MMR for diversity and redundancy elimination
7. Subword Vectorization - Character n-grams for morphological similarity

Deterministic | Explainable | NumPy-Only | Optimized for Indonesian
══════════════════════════════════════════════════════════════════════════════════
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from enum import Enum
import re


# ══════════════════════════════════════════════════════════════════════════════
# INDONESIAN LINGUISTIC DATABASE
# ══════════════════════════════════════════════════════════════════════════════

# Indonesian prefixes (awalan)
PREFIXES = [
    'meng', 'meny', 'men', 'mem', 'me',
    'peng', 'peny', 'pen', 'pem', 'pe',
    'di', 'ter', 'ke', 'se', 'ber', 'be', 'per'
]

# Indonesian suffixes (akhiran)
SUFFIXES = [
    'kan', 'an', 'i', 'nya', 'lah', 'kah', 'pun',
    'mu', 'ku', 'ku', 'ku'
]

# Indonesian infixes (sisipan)
INFIXES = ['el', 'em', 'er']

# Particles that should be removed
PARTICLES = {'lah', 'kah', 'pun', 'per'}

# Stop words for Indonesian
STOPWORDS = {
    'yang', 'di', 'ke', 'dari', 'pada', 'dalam', 'untuk', 'dengan', 'ini', 'itu',
    'adalah', 'dan', 'atau', 'juga', 'serta', 'oleh', 'akan', 'dapat', 'bisa',
    'sudah', 'telah', 'sedang', 'masih', 'belum', 'tidak', 'bukan', 'hanya',
    'sangat', 'lebih', 'paling', 'sekali', 'saya', 'aku', 'kamu', 'anda', 'dia',
    'ia', 'kita', 'kami', 'mereka', 'nya', 'ku', 'mu', 'ada', 'menjadi', 'seperti',
    'sebagai', 'bahwa', 'karena', 'jika', 'maka', 'saat', 'ketika', 'setelah',
    'sebelum', 'antara', 'hingga', 'sampai', 'terhadap', 'tentang', 'tersebut',
    'hal', 'satu', 'dua', 'tiga', 'empat', 'lima', 'para', 'semua', 'setiap',
    'beberapa', 'banyak', 'suatu', 'sebuah', 'harus', 'perlu', 'yaitu', 'yakni',
    'namun', 'tetapi', 'walaupun', 'meskipun', 'agar', 'supaya', 'bila', 'kalau',
    'begitu', 'demikian', 'pun', 'lah', 'kah', 'pernah', 'selalu', 'sering',
    'jarang', 'hampir', 'cukup', 'agak', 'terlalu', 'amat', 'bagi', 'demi',
    'tanpa', 'melalui', 'menurut', 'berdasarkan', 'secara', 'maupun', 'ataupun'
}

# Importance signal words
IMPORTANCE_SIGNALS = {
    'tier1': {  # Highest importance
        'penting', 'utama', 'pokok', 'kunci', 'inti', 'fundamental', 'esensial',
        'vital', 'krusial', 'signifikan', 'strategis', 'kesimpulan', 'simpulan',
        'tujuan', 'sasaran', 'definisi', 'pengertian', 'prinsip', 'dasar',
        'merupakan', 'adalah', 'ialah', 'menunjukkan', 'membuktikan', 'dampak',
        'solusi', 'faktor', 'aspek', 'hasil', 'akibat', 'sebab', 'alasan',
        'terbukti', 'fakta', 'bukti', 'data', 'riset', 'penelitian', 'studi'
    },
    'tier2': {  # Medium importance
        'contoh', 'misalnya', 'antara lain', 'dapat', 'mampu', 'selain',
        'pertama', 'kedua', 'ketiga', 'terakhir', 'kemudian', 'selanjutnya',
        'sebaliknya', 'sementara', 'melalui', 'berdasarkan'
    }
}

# Discourse markers
DISCOURSE_MARKERS = {
    'conclusion': {'kesimpulan', 'simpulan', 'jadi', 'oleh karena itu', 'dengan demikian', 
                   'sebagai kesimpulan', 'intinya', 'singkatnya'},
    'emphasis': {'penting', 'perlu', 'harus', 'sangat', 'terutama', 'khususnya'},
    'contrast': {'namun', 'tetapi', 'akan tetapi', 'meskipun', 'walaupun', 'sebaliknya'},
    'addition': {'selain itu', 'di samping itu', 'lebih lanjut', 'tambahan'},
    'cause': {'karena', 'sebab', 'akibat', 'dampak', 'menyebabkan'},
}


# ══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Token:
    text: str
    lower: str
    stem: str
    idx: int
    sent_idx: int
    is_stopword: bool
    char_ngrams: Set[str] = field(default_factory=set)
    
@dataclass
class Sentence:
    text: str
    tokens: List[Token]
    idx: int
    para_idx: int
    position: str  # 'first', 'middle', 'last', 'single'
    
    # BM25 and TextRank scores
    bm25_score: float = 0.0
    textrank_score: float = 0.0
    
    # Multi-feature scores
    position_score: float = 0.0
    length_score: float = 0.0
    lexical_density: float = 0.0
    importance_signal_score: float = 0.0
    discourse_marker_score: float = 0.0
    
    # Lexical chains
    chain_score: float = 0.0
    
    # Final composite score
    final_score: float = 0.0
    selected: bool = False

@dataclass
class LexicalChain:
    """Represents a chain of semantically related words"""
    members: Set[str] = field(default_factory=set)
    sentence_indices: Set[int] = field(default_factory=set)
    strength: float = 0.0


# ══════════════════════════════════════════════════════════════════════════════
# NAZIEF-ADRIANI INDONESIAN STEMMER
# ══════════════════════════════════════════════════════════════════════════════

class IndonesianStemmer:
    """
    Nazief-Adriani Indonesian stemming algorithm.
    
    Rules-based morphological analyzer for Bahasa Indonesia:
    1. Remove particles (lah, kah, pun)
    2. Remove possessive pronouns (ku, mu, nya)
    3. Remove first-order affixes (prefixes and suffixes)
    4. Remove second-order affixes (complex derivations)
    5. Apply recoding rules for phonological variations
    """
    
    def __init__(self):
        self.cache = {}
        
    def stem(self, word: str) -> str:
        """Stem an Indonesian word to its root form"""
        if len(word) <= 3:
            return word
            
        if word in self.cache:
            return self.cache[word]
        
        original = word
        word = word.lower()
        
        # Remove particles
        word = self._remove_particle(word)
        
        # Remove possessive pronouns
        word = self._remove_possessive(word)
        
        # Try to stem with affixes
        stemmed = self._stem_affixes(word)
        
        self.cache[original] = stemmed
        return stemmed
    
    def _remove_particle(self, word: str) -> str:
        """Remove particles: -lah, -kah, -pun"""
        for particle in ['lah', 'kah', 'pun']:
            if word.endswith(particle) and len(word) > len(particle) + 3:
                return word[:-len(particle)]
        return word
    
    def _remove_possessive(self, word: str) -> str:
        """Remove possessive pronouns: -ku, -mu, -nya"""
        for poss in ['nya', 'ku', 'mu']:
            if word.endswith(poss) and len(word) > len(poss) + 3:
                return word[:-len(poss)]
        return word
    
    def _stem_affixes(self, word: str) -> str:
        """Remove prefixes and suffixes"""
        # Try removing suffix first
        word = self._remove_suffix(word)
        
        # Then remove prefix
        word = self._remove_prefix(word)
        
        return word
    
    def _remove_prefix(self, word: str) -> str:
        """Remove Indonesian prefixes with recoding rules"""
        if len(word) <= 3:
            return word
        
        # Check for complex prefixes first
        for prefix in ['meng', 'meny', 'peng', 'peny']:
            if word.startswith(prefix) and len(word) > len(prefix) + 2:
                root = word[len(prefix):]
                # Recoding rules: meng-e -> e, meny-a -> a
                if prefix in ['meng', 'peng'] and root and root[0] in 'aeiou':
                    return root
                if prefix in ['meny', 'peny'] and root:
                    # meny-akit -> sakit
                    return 's' + root
                return root
        
        # Try simpler prefixes
        for prefix in ['men', 'mem', 'pen', 'pem', 'ter', 'ber', 'per', 'di', 'ke', 'se', 'me', 'pe', 'be']:
            if word.startswith(prefix) and len(word) > len(prefix) + 2:
                root = word[len(prefix):]
                # Recoding: mem-beli -> beli, men-dapat -> dapat
                if prefix in ['mem', 'pem'] and root and root[0] in 'bfpv':
                    return root
                if prefix in ['men', 'pen'] and root and root[0] in 'cdtjz':
                    return root
                return root
        
        return word
    
    def _remove_suffix(self, word: str) -> str:
        """Remove Indonesian suffixes"""
        if len(word) <= 3:
            return word
        
        # Try each suffix
        for suffix in ['kan', 'an', 'i']:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[:-len(suffix)]
        
        return word


# ══════════════════════════════════════════════════════════════════════════════
# SUBWORD CHARACTER N-GRAM VECTORIZER
# ══════════════════════════════════════════════════════════════════════════════

class SubwordVectorizer:
    """
    Character n-gram based vectorizer for morphological similarity.
    
    Captures subword features to detect morphological variants:
    - 'pendidikan' and 'mendidik' share 'didik'
    - More robust than pure token matching
    """
    
    def __init__(self, n_min: int = 3, n_max: int = 5):
        self.n_min = n_min
        self.n_max = n_max
    
    def get_ngrams(self, word: str) -> Set[str]:
        """Extract character n-grams from a word"""
        if len(word) < self.n_min:
            return {word}
        
        ngrams = set()
        word = f"#{word}#"  # Add boundary markers
        
        for n in range(self.n_min, self.n_max + 1):
            for i in range(len(word) - n + 1):
                ngrams.add(word[i:i+n])
        
        return ngrams
    
    def similarity(self, ngrams1: Set[str], ngrams2: Set[str]) -> float:
        """Compute Jaccard similarity between two n-gram sets"""
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)
        
        return intersection / union if union > 0 else 0.0


# ══════════════════════════════════════════════════════════════════════════════
# BM25 SCORING ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class BM25:
    """
    BM25 (Best Matching 25) - State-of-the-art information retrieval weighting.
    
    More effective than TF-IDF for short documents:
    - Non-linear term frequency saturation
    - Document length normalization
    - Proven effectiveness in search and summarization
    
    Parameters:
    - k1: Term frequency saturation (default: 1.5)
    - b: Length normalization (default: 0.75)
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_freqs = Counter()
        self.doc_lengths = []
        self.avg_doc_length = 0.0
        self.num_docs = 0
        self.idf_cache = {}
    
    def fit(self, documents: List[List[str]]):
        """Build document frequency statistics"""
        self.num_docs = len(documents)
        self.doc_lengths = [len(doc) for doc in documents]
        self.avg_doc_length = np.mean(self.doc_lengths) if self.doc_lengths else 0.0
        
        # Count document frequencies
        for doc in documents:
            unique_terms = set(doc)
            for term in unique_terms:
                self.doc_freqs[term] += 1
        
        # Precompute IDF
        for term in self.doc_freqs:
            self.idf_cache[term] = self._compute_idf(term)
    
    def _compute_idf(self, term: str) -> float:
        """Compute IDF for a term"""
        df = self.doc_freqs.get(term, 0)
        # IDF with smoothing: log((N - df + 0.5) / (df + 0.5))
        idf = np.log((self.num_docs - df + 0.5) / (df + 0.5) + 1.0)
        return max(idf, 0.0)
    
    def get_scores(self, query: List[str]) -> np.ndarray:
        """Compute BM25 scores for all documents given a query"""
        scores = np.zeros(self.num_docs)
        
        query_freqs = Counter(query)
        
        for term, qtf in query_freqs.items():
            idf = self.idf_cache.get(term, 0.0)
            
            for doc_idx, doc_length in enumerate(self.doc_lengths):
                # Term frequency in document
                tf = self.doc_freqs.get(term, 0)  # Simplified for sentence-level
                
                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
                
                scores[doc_idx] += idf * (numerator / denominator)
        
        return scores
    
    def compute_similarity_matrix(self, documents: List[List[str]]) -> np.ndarray:
        """Compute pairwise BM25-based similarity matrix"""
        n = len(documents)
        sim_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i, n):
                if i == j:
                    sim_matrix[i, j] = 1.0
                else:
                    # Use word overlap with BM25 weighting
                    doc_i_set = set(documents[i])
                    doc_j_set = set(documents[j])
                    common = doc_i_set & doc_j_set
                    
                    if not common:
                        sim_matrix[i, j] = sim_matrix[j, i] = 0.0
                        continue
                    
                    # Weighted overlap
                    score = 0.0
                    for term in common:
                        idf = self.idf_cache.get(term, 0.0)
                        score += idf
                    
                    # Normalize by document lengths
                    norm = np.sqrt(len(doc_i_set) * len(doc_j_set))
                    sim_matrix[i, j] = sim_matrix[j, i] = score / norm if norm > 0 else 0.0
        
        return sim_matrix


# ══════════════════════════════════════════════════════════════════════════════
# TEXTRANK ALGORITHM
# ══════════════════════════════════════════════════════════════════════════════

class TextRank:
    """
    TextRank: Graph-based ranking algorithm for text.
    
    Similar to PageRank but for sentences:
    1. Build similarity graph between sentences
    2. Iteratively propagate scores through graph
    3. Converge to stable importance ranking
    
    More robust than simple similarity scoring because:
    - Considers global document structure
    - Reinforces importance through graph connectivity
    - Naturally handles redundancy
    """
    
    def __init__(self, damping: float = 0.85, max_iter: int = 100, tol: float = 1e-4):
        self.damping = damping
        self.max_iter = max_iter
        self.tol = tol
    
    def rank(self, similarity_matrix: np.ndarray) -> np.ndarray:
        """
        Compute TextRank scores for sentences.
        
        Args:
            similarity_matrix: n x n matrix of sentence similarities
            
        Returns:
            scores: n-length array of TextRank importance scores
        """
        n = len(similarity_matrix)
        if n == 0:
            return np.array([])
        if n == 1:
            return np.array([1.0])
        
        # Initialize scores uniformly
        scores = np.ones(n) / n
        
        # Build transition matrix
        # Normalize rows to sum to 1
        row_sums = similarity_matrix.sum(axis=1, keepdims=True)
        row_sums = np.where(row_sums == 0, 1, row_sums)
        transition = similarity_matrix / row_sums
        
        # Iterative power method
        for iteration in range(self.max_iter):
            prev_scores = scores.copy()
            
            # TextRank formula: TR(Vi) = (1-d) + d * sum(TR(Vj) / |Out(Vj)|)
            scores = (1 - self.damping) / n + self.damping * transition.T @ scores
            
            # Check convergence
            diff = np.abs(scores - prev_scores).sum()
            if diff < self.tol:
                break
        
        # Normalize to [0, 1]
        if scores.max() > 0:
            scores = scores / scores.max()
        
        return scores


# ══════════════════════════════════════════════════════════════════════════════
# LEXICAL CHAIN ANALYZER
# ══════════════════════════════════════════════════════════════════════════════

class LexicalChainAnalyzer:
    """
    Lexical chain analysis for discourse-level importance.
    
    Tracks recurring concepts (after stemming) across the document:
    - Words that appear multiple times form chains
    - Chains indicate central concepts
    - Sentences containing chain members are more important
    """
    
    def __init__(self, stemmer: IndonesianStemmer, subword_vec: SubwordVectorizer):
        self.stemmer = stemmer
        self.subword_vec = subword_vec
        self.chains: List[LexicalChain] = []
    
    def build_chains(self, sentences: List[Sentence], min_chain_length: int = 2):
        """Build lexical chains from sentences"""
        # Collect all stems with their sentence indices
        stem_to_sents = defaultdict(set)
        
        for sent in sentences:
            for token in sent.tokens:
                if not token.is_stopword:
                    stem_to_sents[token.stem].add(sent.idx)
        
        # Create chains for stems that appear in multiple sentences
        for stem, sent_indices in stem_to_sents.items():
            if len(sent_indices) >= min_chain_length:
                chain = LexicalChain(
                    members={stem},
                    sentence_indices=sent_indices,
                    strength=len(sent_indices)
                )
                self.chains.append(chain)
        
        # Sort chains by strength
        self.chains.sort(key=lambda c: c.strength, reverse=True)
    
    def score_sentences(self, sentences: List[Sentence]) -> np.ndarray:
        """Compute chain-based importance scores for sentences"""
        scores = np.zeros(len(sentences))
        
        for chain in self.chains:
            for sent_idx in chain.sentence_indices:
                if sent_idx < len(scores):
                    # Weight by chain strength
                    scores[sent_idx] += chain.strength
        
        # Normalize
        if scores.max() > 0:
            scores = scores / scores.max()
        
        return scores


# ══════════════════════════════════════════════════════════════════════════════
# MULTI-FEATURE SENTENCE SCORER
# ══════════════════════════════════════════════════════════════════════════════

class SentenceScorer:
    """
    Multi-feature robust sentence scoring.
    
    Combines multiple signals for importance detection:
    1. Position: First/last sentences often important (Indonesian structure)
    2. Length: Normalize scores by sentence length
    3. Lexical density: Ratio of content words to total words
    4. Importance signals: Presence of key indicator words
    5. Discourse markers: Conclusion, emphasis, etc.
    """
    
    @staticmethod
    def compute_position_score(sent: Sentence, total_sents: int) -> float:
        """
        Position-based scoring for Indonesian text structure.
        
        Indonesian academic/formal texts often:
        - Start with thesis/main idea
        - End with conclusion
        - Have important points at paragraph beginnings
        """
        score = 0.0
        
        # Sentence position in document
        if sent.idx == 0:  # First sentence
            score += 0.4
        elif sent.idx == total_sents - 1:  # Last sentence
            score += 0.3
        elif sent.idx < 3:  # Early sentences
            score += 0.2
        elif sent.idx >= total_sents - 3:  # Late sentences
            score += 0.15
        
        # Position within paragraph
        if sent.position == 'first':
            score += 0.3
        elif sent.position == 'last':
            score += 0.2
        elif sent.position == 'single':
            score += 0.4
        
        return min(score, 1.0)
    
    @staticmethod
    def compute_length_score(sent: Sentence) -> float:
        """
        Length normalization score.
        
        Prefer sentences of moderate length:
        - Too short: May lack information
        - Too long: May be complex/unfocused
        """
        num_tokens = len([t for t in sent.tokens if not t.is_stopword])
        
        # Ideal range: 8-20 content words
        if 8 <= num_tokens <= 20:
            return 1.0
        elif 5 <= num_tokens < 8:
            return 0.7 + (num_tokens - 5) * 0.1
        elif 20 < num_tokens <= 30:
            return 1.0 - (num_tokens - 20) * 0.03
        elif num_tokens < 5:
            return num_tokens * 0.15
        else:
            return max(0.4, 1.0 - (num_tokens - 30) * 0.02)
    
    @staticmethod
    def compute_lexical_density(sent: Sentence) -> float:
        """
        Lexical density: ratio of content words to total words.
        
        Higher density indicates information-rich sentences.
        """
        if not sent.tokens:
            return 0.0
        
        content_words = [t for t in sent.tokens if not t.is_stopword]
        density = len(content_words) / len(sent.tokens)
        
        return density
    
    @staticmethod
    def compute_importance_signal_score(sent: Sentence) -> float:
        """
        Score based on presence of importance signal words.
        """
        score = 0.0
        text_lower = sent.text.lower()
        
        # Check tier1 signals (highest importance)
        for signal in IMPORTANCE_SIGNALS['tier1']:
            if signal in text_lower:
                score += 0.3
        
        # Check tier2 signals
        for signal in IMPORTANCE_SIGNALS['tier2']:
            if signal in text_lower:
                score += 0.15
        
        return min(score, 1.0)
    
    @staticmethod
    def compute_discourse_marker_score(sent: Sentence) -> float:
        """
        Score based on discourse markers (conclusion, emphasis, etc.)
        """
        score = 0.0
        text_lower = sent.text.lower()
        
        # Conclusion markers are very strong signals
        for marker in DISCOURSE_MARKERS['conclusion']:
            if marker in text_lower:
                score += 0.5
        
        # Emphasis markers
        for marker in DISCOURSE_MARKERS['emphasis']:
            if marker in text_lower:
                score += 0.2
        
        # Contrast markers (medium importance)
        for marker in DISCOURSE_MARKERS['contrast']:
            if marker in text_lower:
                score += 0.15
        
        # Addition/cause markers
        for marker in DISCOURSE_MARKERS['addition']:
            if marker in text_lower:
                score += 0.1
        for marker in DISCOURSE_MARKERS['cause']:
            if marker in text_lower:
                score += 0.1
        
        return min(score, 1.0)


# ══════════════════════════════════════════════════════════════════════════════
# COVERAGE-BASED SUMMARY SELECTOR (MMR)
# ══════════════════════════════════════════════════════════════════════════════

class MMRSelector:
    """
    Maximal Marginal Relevance (MMR) for coverage-based summary selection.
    
    Selects sentences that:
    1. Have high importance scores (relevance)
    2. Are diverse/non-redundant (coverage)
    
    Formula: MMR = λ * Relevance - (1-λ) * MaxSimilarity
    
    Balances quality and diversity for comprehensive summaries.
    """
    
    def __init__(self, lambda_param: float = 0.7):
        self.lambda_param = lambda_param
    
    def select(self, 
               sentences: List[Sentence],
               similarity_matrix: np.ndarray,
               num_sentences: int) -> List[int]:
        """
        Select sentences using MMR algorithm.
        
        Args:
            sentences: List of sentence objects with scores
            similarity_matrix: Pairwise similarity matrix
            num_sentences: Number of sentences to select
            
        Returns:
            selected_indices: List of selected sentence indices
        """
        if num_sentences <= 0 or not sentences:
            return []
        
        num_sentences = min(num_sentences, len(sentences))
        selected = []
        unselected = set(range(len(sentences)))
        
        # Get relevance scores
        relevance = np.array([s.final_score for s in sentences])
        
        # Select first sentence (highest relevance)
        first_idx = np.argmax(relevance)
        selected.append(first_idx)
        unselected.remove(first_idx)
        
        # Iteratively select remaining sentences
        for _ in range(num_sentences - 1):
            if not unselected:
                break
            
            mmr_scores = {}
            
            for idx in unselected:
                # Relevance component
                rel = relevance[idx]
                
                # Redundancy component (max similarity to selected)
                max_sim = max(similarity_matrix[idx, s] for s in selected)
                
                # MMR formula
                mmr = self.lambda_param * rel - (1 - self.lambda_param) * max_sim
                mmr_scores[idx] = mmr
            
            # Select sentence with highest MMR
            best_idx = max(mmr_scores, key=mmr_scores.get)
            selected.append(best_idx)
            unselected.remove(best_idx)
        
        # Sort selected indices by document order
        selected.sort()
        
        return selected


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ANALYZER: RINGKASION v2.0.0
# ══════════════════════════════════════════════════════════════════════════════

class RINGKASION:
    """
    RINGKASION v2.0.0 - Advanced Indonesian Text Summarization Engine
    
    Integrates all components for state-of-the-art Indonesian summarization.
    """
    
    def __init__(self):
        self.stemmer = IndonesianStemmer()
        self.subword_vec = SubwordVectorizer(n_min=3, n_max=5)
        self.bm25 = BM25(k1=1.5, b=0.75)
        self.textrank = TextRank(damping=0.85, max_iter=100)
        self.chain_analyzer = LexicalChainAnalyzer(self.stemmer, self.subword_vec)
        self.scorer = SentenceScorer()
        self.mmr_selector = MMRSelector(lambda_param=0.7)
        
        # Parsed structures
        self.sentences: List[Sentence] = []
        self.paragraphs: List[List[Sentence]] = []
        self.similarity_matrix = None
    
    def analyze(self, text: str, summary_ratio: float = 0.3) -> Dict:
        """
        Analyze text and generate summary.
        
        Args:
            text: Input Indonesian text
            summary_ratio: Ratio of sentences to include in summary (0.0-1.0)
            
        Returns:
            result: Dictionary containing analysis results
        """
        # Step 1: Parse text
        self._parse_text(text)
        
        if not self.sentences:
            return self._empty_result()
        
        # Step 2: Build document representations
        documents = [[t.stem for t in s.tokens if not t.is_stopword] 
                     for s in self.sentences]
        
        # Step 3: Fit BM25
        self.bm25.fit(documents)
        
        # Step 4: Compute BM25-based similarity matrix
        self.similarity_matrix = self.bm25.compute_similarity_matrix(documents)
        
        # Step 5: TextRank scoring
        textrank_scores = self.textrank.rank(self.similarity_matrix)
        for i, score in enumerate(textrank_scores):
            if i < len(self.sentences):
                self.sentences[i].textrank_score = score
        
        # Step 6: Lexical chain analysis
        self.chain_analyzer.build_chains(self.sentences, min_chain_length=2)
        chain_scores = self.chain_analyzer.score_sentences(self.sentences)
        for i, score in enumerate(chain_scores):
            if i < len(self.sentences):
                self.sentences[i].chain_score = score
        
        # Step 7: Multi-feature scoring
        for sent in self.sentences:
            sent.position_score = self.scorer.compute_position_score(sent, len(self.sentences))
            sent.length_score = self.scorer.compute_length_score(sent)
            sent.lexical_density = self.scorer.compute_lexical_density(sent)
            sent.importance_signal_score = self.scorer.compute_importance_signal_score(sent)
            sent.discourse_marker_score = self.scorer.compute_discourse_marker_score(sent)
        
        # Step 8: Compute final composite scores
        self._compute_final_scores()
        
        # Step 9: Select summary sentences using MMR
        num_summary_sents = max(1, int(len(self.sentences) * summary_ratio))
        selected_indices = self.mmr_selector.select(
            self.sentences, 
            self.similarity_matrix, 
            num_summary_sents
        )
        
        # Mark selected sentences
        for idx in selected_indices:
            if idx < len(self.sentences):
                self.sentences[idx].selected = True
        
        # Step 10: Generate result
        return self._generate_result()
    
    def _parse_text(self, text: str):
        """Parse text into sentences and tokens"""
        # Clean text
        text = self._clean_text(text)
        
        # Split into paragraphs
        paragraphs = self._split_paragraphs(text)
        
        sent_idx = 0
        for para_idx, para_text in enumerate(paragraphs):
            # Split paragraph into sentences
            sentences = self._split_sentences(para_text)
            para_sentences = []
            
            for i, sent_text in enumerate(sentences):
                if not sent_text.strip():
                    continue
                
                # Determine position
                if len(sentences) == 1:
                    position = 'single'
                elif i == 0:
                    position = 'first'
                elif i == len(sentences) - 1:
                    position = 'last'
                else:
                    position = 'middle'
                
                # Tokenize
                tokens = self._tokenize(sent_text)
                
                # Create sentence object
                sent = Sentence(
                    text=sent_text,
                    tokens=tokens,
                    idx=sent_idx,
                    para_idx=para_idx,
                    position=position
                )
                
                para_sentences.append(sent)
                self.sentences.append(sent)
                sent_idx += 1
            
            if para_sentences:
                self.paragraphs.append(para_sentences)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs"""
        paragraphs = re.split(r'\n\s*\n+', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split paragraph into sentences"""
        # Simple sentence splitting on period, exclamation, question mark
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _tokenize(self, text: str) -> List[Token]:
        """Tokenize sentence into tokens"""
        # Simple word tokenization
        words = re.findall(r'\b\w+\b', text.lower())
        
        tokens = []
        for idx, word in enumerate(words):
            is_stopword = word in STOPWORDS
            stem = self.stemmer.stem(word)
            char_ngrams = self.subword_vec.get_ngrams(word)
            
            token = Token(
                text=word,
                lower=word,
                stem=stem,
                idx=idx,
                sent_idx=len(self.sentences),
                is_stopword=is_stopword,
                char_ngrams=char_ngrams
            )
            tokens.append(token)
        
        return tokens
    
    def _compute_final_scores(self):
        """Compute final composite scores for all sentences"""
        # Weights for different features
        weights = {
            'textrank': 0.30,      # TextRank is primary
            'chain': 0.15,         # Lexical chains
            'position': 0.20,      # Position
            'length': 0.10,        # Length normalization
            'lexical_density': 0.10,  # Lexical density
            'importance': 0.10,    # Importance signals
            'discourse': 0.05      # Discourse markers
        }
        
        for sent in self.sentences:
            score = (
                weights['textrank'] * sent.textrank_score +
                weights['chain'] * sent.chain_score +
                weights['position'] * sent.position_score +
                weights['length'] * sent.length_score +
                weights['lexical_density'] * sent.lexical_density +
                weights['importance'] * sent.importance_signal_score +
                weights['discourse'] * sent.discourse_marker_score
            )
            sent.final_score = score
    
    def _generate_result(self) -> Dict:
        """Generate analysis result"""
        # Get top sentences
        sorted_sents = sorted(self.sentences, key=lambda s: s.final_score, reverse=True)
        top_sentences = sorted_sents[:5]
        
        # Generate summary
        selected_sents = [s for s in self.sentences if s.selected]
        summary = ' '.join(s.text for s in selected_sents)
        
        # Extract key information
        topik_utama = sorted_sents[0].text if sorted_sents else ""
        
        # Gagasan pokok per paragraph
        gagasan_pokok = []
        for para_idx, para_sents in enumerate(self.paragraphs):
            if para_sents:
                best_sent = max(para_sents, key=lambda s: s.final_score)
                gagasan_pokok.append((para_idx + 1, best_sent.text))
        
        # Top lexical chains
        top_chains = self.chain_analyzer.chains[:10]
        
        result = {
            'summary': summary,
            'topik_utama': topik_utama,
            'gagasan_pokok': gagasan_pokok,
            'top_sentences': [(s.text, s.final_score) for s in top_sentences],
            'lexical_chains': [(list(c.members), c.strength) for c in top_chains],
            'num_sentences': len(self.sentences),
            'num_paragraphs': len(self.paragraphs),
            'summary_ratio': len(selected_sents) / len(self.sentences) if self.sentences else 0.0
        }
        
        return result
    
    def _empty_result(self) -> Dict:
        """Return empty result for invalid input"""
        return {
            'summary': '',
            'topik_utama': '',
            'gagasan_pokok': [],
            'top_sentences': [],
            'lexical_chains': [],
            'num_sentences': 0,
            'num_paragraphs': 0,
            'summary_ratio': 0.0
        }


# ══════════════════════════════════════════════════════════════════════════════
# OUTPUT FORMATTER
# ══════════════════════════════════════════════════════════════════════════════

class OutputFormatter:
    """Format analysis results for display"""
    
    @staticmethod
    def format(result: Dict) -> str:
        """Format result as readable text"""
        lines = []
        lines.append("=" * 80)
        lines.append("  RINGKASION v2.0.0 - HASIL ANALISIS")
        lines.append("=" * 80)
        lines.append("")
        
        # Statistics
        lines.append(f"[Statistik]")
        lines.append(f"  Paragraf: {result['num_paragraphs']} | "
                    f"Kalimat: {result['num_sentences']} | "
                    f"Ratio Ringkasan: {result['summary_ratio']:.1%}")
        lines.append("")
        
        # Topik utama
        lines.append("-" * 80)
        lines.append("[TOPIK UTAMA]")
        lines.append(f"  {result['topik_utama']}")
        lines.append("")
        
        # Gagasan pokok
        lines.append("-" * 80)
        lines.append("[GAGASAN POKOK TIAP PARAGRAF]")
        lines.append("")
        for para_num, text in result['gagasan_pokok']:
            lines.append(f"  Paragraf {para_num}:")
            lines.append(f"    {text}")
            lines.append("")
        
        # Top sentences
        lines.append("-" * 80)
        lines.append("[KALIMAT PENTING]")
        lines.append("")
        for i, (text, score) in enumerate(result['top_sentences'][:5], 1):
            lines.append(f"  [{i}] Skor: {score:.3f}")
            lines.append(f"    {text}")
            lines.append("")
        
        # Lexical chains
        if result['lexical_chains']:
            lines.append("-" * 80)
            lines.append("[RANTAI LEKSIKAL]")
            lines.append("  Konsep yang sering muncul:")
            lines.append("")
            for members, strength in result['lexical_chains'][:10]:
                members_str = ', '.join(sorted(members)[:5])
                lines.append(f"    • {members_str} (kekuatan: {strength:.0f})")
            lines.append("")
        
        # Summary
        lines.append("-" * 80)
        lines.append("[RANGKUMAN]")
        lines.append(f"  {result['summary']}")
        lines.append("")
        
        lines.append("=" * 80)
        lines.append("  Analisis selesai dengan RINGKASION v2.0.0")
        lines.append("=" * 80)
        
        return '\n'.join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# SAMPLE TEXT & MAIN
# ══════════════════════════════════════════════════════════════════════════════

def get_sample_text() -> str:
    """Get sample Indonesian text for testing"""
    return """
Pendidikan merupakan fondasi utama dalam pembangunan suatu bangsa. Melalui pendidikan yang berkualitas, sebuah negara dapat menciptakan sumber daya manusia yang kompeten dan berdaya saing tinggi. Oleh karena itu, investasi dalam bidang pendidikan menjadi sangat penting dan strategis untuk kemajuan bangsa.

Sistem pendidikan Indonesia telah mengalami berbagai transformasi sejak kemerdekaan. Kurikulum terus diperbarui untuk menyesuaikan dengan perkembangan zaman dan kebutuhan dunia kerja. Namun demikian, masih terdapat berbagai tantangan yang harus dihadapi, seperti kesenjangan kualitas pendidikan antara daerah perkotaan dan pedesaan, serta keterbatasan infrastruktur di beberapa wilayah.

Pemerintah telah melakukan berbagai upaya untuk meningkatkan kualitas pendidikan nasional. Program wajib belajar 12 tahun telah diterapkan untuk memastikan setiap anak Indonesia mendapatkan akses pendidikan dasar dan menengah. Selain itu, bantuan operasional sekolah dan beasiswa diberikan untuk meringankan beban biaya pendidikan bagi masyarakat kurang mampu.

Teknologi digital juga telah membawa perubahan signifikan dalam dunia pendidikan. Pembelajaran daring menjadi alternatif yang efektif, terutama di masa pandemi. Platform e-learning dan aplikasi pendidikan semakin berkembang, memberikan akses pembelajaran yang lebih luas kepada masyarakat. Dengan demikian, pendidikan tidak lagi terbatas oleh ruang dan waktu.

Kesimpulannya, pendidikan merupakan kunci utama untuk mencapai kemajuan bangsa. Diperlukan kerja sama antara pemerintah, masyarakat, dan sektor swasta untuk terus meningkatkan kualitas pendidikan Indonesia. Hanya dengan pendidikan yang berkualitas, Indonesia dapat bersaing di tingkat global dan mewujudkan cita-cita mencerdaskan kehidupan bangsa.
    """


def main():
    """Main entry point"""
    import sys
    
    # Get input text
    if len(sys.argv) > 1:
        # From file
        try:
            with open(sys.argv[1], 'r', encoding='utf-8') as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Error: File '{sys.argv[1]}' tidak ditemukan.")
            print("Menggunakan teks contoh...")
            text = get_sample_text()
    else:
        # Check stdin
        if not sys.stdin.isatty():
            text = sys.stdin.read()
        else:
            text = get_sample_text()
    
    if not text.strip():
        text = get_sample_text()
    
    # Analyze
    analyzer = RINGKASION()
    result = analyzer.analyze(text, summary_ratio=0.3)
    
    # Format and output
    output = OutputFormatter.format(result)
    print(output)
    
    # Save to file if specified
    if len(sys.argv) > 2:
        with open(sys.argv[2], 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"\nOutput disimpan ke: {sys.argv[2]}")


if __name__ == "__main__":
    main()
