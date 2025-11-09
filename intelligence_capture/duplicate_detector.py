#!/usr/bin/env python3
"""
Duplicate Detector Component for Knowledge Graph Consolidation

Identifies similar entities using:
- Fuzzy string matching (name similarity)
- Semantic similarity (embedding-based)
- Entity-specific normalization rules

Supports configurable similarity thresholds per entity type.
"""
import re
import time
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher
from datetime import datetime
import json

from intelligence_capture.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


class EmbeddingError(Exception):
    """Custom exception for embedding generation failures"""
    pass

# Optional: Use rapidfuzz for better performance (fallback to difflib)
try:
    from rapidfuzz import fuzz
    HAVE_RAPIDFUZZ = True
except ImportError:
    HAVE_RAPIDFUZZ = False

# Optional: Use OpenAI for semantic similarity
try:
    from openai import OpenAI
    HAVE_OPENAI = True
except ImportError:
    HAVE_OPENAI = False


class DuplicateDetector:
    """
    Detects duplicate entities using fuzzy matching and semantic similarity
    
    Features:
    - Entity-specific name normalization
    - Configurable similarity thresholds per entity type
    - Embedding cache to avoid redundant API calls
    - Combined fuzzy + semantic similarity scoring
    """
    
    def __init__(self, config: Dict, openai_api_key: Optional[str] = None, db=None):
        """
        Initialize duplicate detector
        
        Args:
            config: Configuration dict with similarity_thresholds and similarity_weights
            openai_api_key: Optional OpenAI API key for semantic similarity
            db: Optional database instance for persistent embedding storage
        """
        self.config = config
        self.similarity_thresholds = config.get("similarity_thresholds", {})
        self.similarity_weights = config.get("similarity_weights", {
            "semantic_weight": 0.3,
            "name_weight": 0.7
        })
        
        # Performance settings
        self.max_candidates = config.get("performance", {}).get("max_candidates", 10)
        self.enable_caching = config.get("performance", {}).get("enable_caching", True)
        self.use_db_storage = config.get("performance", {}).get("use_db_storage", True)
        
        # Retry and circuit breaker settings
        self.max_retries = config.get("retry", {}).get("max_retries", 3)
        self.circuit_breaker_threshold = config.get("retry", {}).get("circuit_breaker_threshold", 10)
        
        # Circuit breaker state
        self.consecutive_failures = 0
        self.circuit_breaker_open = False
        self.circuit_breaker_opened_at = None
        
        # Embedding cache (in-memory for current session)
        self.embedding_cache = {} if self.enable_caching else None
        
        # Database for persistent embedding storage
        self.db = db
        
        # Statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.db_hits = 0
        self.db_misses = 0
        
        # Initialize OpenAI client if available
        self.openai_client = None
        if HAVE_OPENAI and openai_api_key:
            self.openai_client = OpenAI(api_key=openai_api_key)
    
    def find_duplicates(
        self,
        entity: Dict,
        entity_type: str,
        existing_entities: List[Dict]
    ) -> List[Tuple[Dict, float]]:
        """
        Find duplicate entities using fuzzy-first filtering + semantic matching
        
        Strategy:
        1. Use fuzzy matching to filter candidates (fast, no API calls)
        2. Only compute semantic similarity for top candidates (slow, API calls)
        3. Skip semantic if fuzzy score >= 0.95 (obvious duplicate)
        
        This reduces API calls by 90-95% compared to comparing against all entities.
        
        Args:
            entity: Entity to match (must have 'name' or 'description' field)
            entity_type: Type of entity (systems, pain_points, etc.)
            existing_entities: List of existing entities to compare against
            
        Returns:
            List of (entity, similarity_score) tuples above threshold,
            sorted by similarity score (highest first), limited to max_candidates
        """
        if not existing_entities:
            return []
        
        # Get entity text for comparison
        entity_text = self._get_entity_text(entity, entity_type)
        if not entity_text:
            return []
        
        # Get similarity threshold for this entity type
        threshold = self._get_similarity_threshold(entity_type)
        
        # STAGE 1: Fuzzy matching to filter candidates (fast, no API calls)
        fuzzy_candidates = []
        for existing in existing_entities:
            existing_text = self._get_entity_text(existing, entity_type)
            if not existing_text:
                continue
            
            # Calculate fuzzy similarity only
            fuzzy_score = self.calculate_name_similarity(
                entity_text,
                existing_text,
                entity_type
            )
            
            # Keep candidates above a lower threshold for fuzzy filtering
            # Use 70% of the target threshold to be more inclusive at this stage
            fuzzy_threshold = threshold * 0.7
            if fuzzy_score >= fuzzy_threshold:
                fuzzy_candidates.append((existing, existing_text, fuzzy_score))
        
        # Sort by fuzzy score and take top candidates
        fuzzy_candidates.sort(key=lambda x: x[2], reverse=True)
        top_fuzzy_candidates = fuzzy_candidates[:self.max_candidates * 2]  # Take 2x for safety
        
        logger.debug(f"Fuzzy filtering: {len(existing_entities)} → {len(top_fuzzy_candidates)} candidates")
        
        # STAGE 2: Semantic similarity for top candidates only (slow, API calls)
        final_candidates = []
        skip_semantic_threshold = self.config.get("performance", {}).get("skip_semantic_threshold", 0.95)
        
        for existing, existing_text, fuzzy_score in top_fuzzy_candidates:
            # If fuzzy score is very high (>= 0.95), skip semantic similarity
            if fuzzy_score >= skip_semantic_threshold:
                logger.debug(f"Skipping semantic for obvious duplicate (fuzzy={fuzzy_score:.2f})")
                final_candidates.append((existing, fuzzy_score))
                continue
            
            # Calculate combined similarity (fuzzy + semantic)
            combined_score = self._calculate_combined_similarity(
                entity_text,
                existing_text,
                entity_type
            )
            
            # Only include if above threshold
            if combined_score >= threshold:
                final_candidates.append((existing, combined_score))
        
        # Sort by similarity (highest first) and limit to max_candidates
        final_candidates.sort(key=lambda x: x[1], reverse=True)
        result = final_candidates[:self.max_candidates]
        
        logger.debug(f"Final candidates: {len(result)} above threshold {threshold:.2f}")
        return result
    
    def calculate_name_similarity(
        self,
        name1: str,
        name2: str,
        entity_type: str
    ) -> float:
        """
        Calculate fuzzy string similarity with entity-specific normalization
        
        Args:
            name1: First entity name
            name2: Second entity name
            entity_type: Type of entity (for normalization rules)
            
        Returns:
            Similarity score (0.0-1.0)
        """
        # Normalize names
        norm1 = self.normalize_name(name1, entity_type)
        norm2 = self.normalize_name(name2, entity_type)
        
        if not norm1 or not norm2:
            return 0.0
        
        # Use rapidfuzz if available (faster), otherwise difflib
        if HAVE_RAPIDFUZZ:
            # Token sort ratio handles word order differences
            return fuzz.token_sort_ratio(norm1, norm2) / 100.0
        else:
            # Fallback to difflib SequenceMatcher
            return SequenceMatcher(None, norm1, norm2).ratio()
    
    def normalize_name(self, name: str, entity_type: str) -> str:
        """
        Normalize entity name with entity-specific rules
        
        Args:
            name: Entity name to normalize
            entity_type: Type of entity
            
        Returns:
            Normalized name (lowercase, common words removed)
        """
        if not name:
            return ""
        
        # Convert to lowercase
        normalized = name.lower().strip()
        
        # Entity-specific normalization rules
        if entity_type == "systems":
            # Remove common system-related words
            common_words = [
                "sistema", "software", "herramienta", "aplicación",
                "system", "tool", "application", "app", "plataforma", "platform"
            ]
            for word in common_words:
                normalized = re.sub(rf'\b{word}\b', '', normalized, flags=re.IGNORECASE)
        
        elif entity_type == "pain_points":
            # Remove common pain point prefixes
            common_prefixes = [
                "problema de", "problema con", "dificultad con", "issue with",
                "problem with", "challenge with", "pain point:"
            ]
            for prefix in common_prefixes:
                normalized = re.sub(rf'^{prefix}\s*', '', normalized, flags=re.IGNORECASE)
        
        elif entity_type == "processes":
            # Remove common process words
            common_words = ["proceso", "process", "procedimiento", "procedure"]
            for word in common_words:
                normalized = re.sub(rf'\b{word}\b', '', normalized, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def calculate_semantic_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """
        Calculate semantic similarity using OpenAI embeddings + cosine similarity
        
        Falls back to 0.0 if:
        - OpenAI client not available
        - Circuit breaker is open
        - Embedding generation fails after retries
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0.0-1.0), or 0.0 if unavailable/failed
        """
        if not self.openai_client or not text1 or not text2:
            return 0.0
        
        # Check circuit breaker
        if self.circuit_breaker_open:
            return 0.0
        
        try:
            # Get embeddings (with caching and retry logic)
            emb1 = self._get_embedding(text1)
            emb2 = self._get_embedding(text2)
            
            # If either embedding is None (cache miss + API failure), return 0.0
            # This triggers fallback to fuzzy-only matching
            if emb1 is None or emb2 is None:
                return 0.0
            
            # Calculate cosine similarity
            return self._cosine_similarity(emb1, emb2)
            
        except EmbeddingError as e:
            # Embedding generation failed after all retries
            # Fall back to fuzzy-only matching (return 0.0 for semantic component)
            logger.warning("Falling back to fuzzy-only matching due to embedding error")
            return 0.0
            
        except Exception as e:
            # Unexpected error
            logger.warning(f"Unexpected semantic similarity error: {e}")
            return 0.0
    
    def _calculate_combined_similarity(
        self,
        text1: str,
        text2: str,
        entity_type: str
    ) -> float:
        """
        Calculate combined similarity using weighted fuzzy + semantic matching
        
        Args:
            text1: First entity text
            text2: Second entity text
            entity_type: Type of entity
            
        Returns:
            Combined similarity score (0.0-1.0)
        """
        # Calculate name similarity (fuzzy matching)
        name_sim = self.calculate_name_similarity(text1, text2, entity_type)
        
        # Calculate semantic similarity (if available)
        semantic_sim = 0.0
        if self.openai_client:
            semantic_sim = self.calculate_semantic_similarity(text1, text2)
        
        # Combine using configured weights
        name_weight = self.similarity_weights.get("name_weight", 0.7)
        semantic_weight = self.similarity_weights.get("semantic_weight", 0.3)
        
        # If semantic similarity not available, use only name similarity
        if semantic_sim == 0.0:
            return name_sim
        
        combined = (name_weight * name_sim) + (semantic_weight * semantic_sim)
        return min(1.0, max(0.0, combined))
    
    def _get_entity_text(self, entity: Dict, entity_type: str) -> str:
        """
        Extract text from entity for comparison
        
        Improved logic:
        - Combines name AND description for better semantic matching
        - Truncates description to 200 chars to avoid overwhelming name
        - Handles missing fields gracefully
        
        Args:
            entity: Entity dict
            entity_type: Type of entity
            
        Returns:
            Text to use for similarity comparison (name + truncated description)
        """
        # Extract name (try multiple field names)
        name = ""
        if "name" in entity and entity["name"]:
            name = str(entity["name"]).strip()
        elif "title" in entity and entity["title"]:
            name = str(entity["title"]).strip()
        elif entity_type == "pain_points" and "type" in entity and entity["type"]:
            name = str(entity["type"]).strip()
        
        # Extract description
        description = ""
        if "description" in entity and entity["description"]:
            description = str(entity["description"]).strip()
        
        # Combine name and description for better semantic matching
        # Truncate description to 200 chars to avoid overwhelming name
        if name and description:
            # Combine: name is more important, description provides context
            truncated_desc = description[:200]
            return f"{name} {truncated_desc}"
        elif name:
            return name
        elif description:
            # If no name, use full description (up to 200 chars)
            return description[:200]
        else:
            # No text available
            return ""
    
    def _get_similarity_threshold(self, entity_type: str) -> float:
        """
        Get similarity threshold for entity type
        
        Args:
            entity_type: Type of entity
            
        Returns:
            Similarity threshold (0.0-1.0)
        """
        return self.similarity_thresholds.get(
            entity_type,
            self.similarity_thresholds.get("default", 0.85)
        )
    
    def _get_embedding(self, text: str, entity_type: str = None, entity_id: int = None) -> Optional[List[float]]:
        """
        Get embedding for text with retry logic and circuit breaker
        
        Implements:
        - Database lookup for pre-computed embeddings (fastest)
        - In-memory cache for current session (fast)
        - OpenAI API call with retry logic (slow)
        - Exponential backoff retry (up to max_retries attempts)
        - Circuit breaker pattern (opens after consecutive_failures threshold)
        - Fallback to None (caller should use fuzzy-only matching)
        
        Args:
            text: Text to embed
            entity_type: Optional entity type for database lookup
            entity_id: Optional entity ID for database lookup
            
        Returns:
            Embedding vector or None if error/circuit breaker open
            
        Raises:
            EmbeddingError: If all retry attempts fail
        """
        # Check in-memory cache first (fastest)
        if self.enable_caching and text in self.embedding_cache:
            self.cache_hits += 1
            return self.embedding_cache[text]
        
        # Check database for pre-computed embedding (fast)
        if self.use_db_storage and self.db and entity_type and entity_id:
            try:
                embedding = self.db.get_entity_embedding(entity_type, entity_id)
                if embedding:
                    self.db_hits += 1
                    # Cache in memory for this session
                    if self.enable_caching:
                        self.embedding_cache[text] = embedding
                    return embedding
                else:
                    self.db_misses += 1
            except Exception as e:
                logger.debug(f"Database embedding lookup error: {e}")
                self.db_misses += 1
        
        # Not in cache or database, need to generate via API
        self.cache_misses += 1
        
        # Check circuit breaker
        if self.circuit_breaker_open:
            logger.warning(f"Circuit breaker OPEN - skipping embedding API call (opened at: {self.circuit_breaker_opened_at}, failures: {self.consecutive_failures})")
            return None
        
        # Retry loop with exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                embedding = response.data[0].embedding
                
                # Success! Reset failure counter
                self.consecutive_failures = 0
                
                # Cache in memory for this session
                if self.enable_caching:
                    self.embedding_cache[text] = embedding
                
                # Store in database for future sessions
                if self.use_db_storage and self.db and entity_type and entity_id:
                    try:
                        self.db.store_entity_embedding(entity_type, entity_id, embedding)
                    except Exception as e:
                        logger.debug(f"Failed to store embedding in database: {e}")
                
                return embedding
                
            except Exception as e:
                last_error = e
                self.consecutive_failures += 1
                
                # Check if we should open circuit breaker
                if self.consecutive_failures >= self.circuit_breaker_threshold:
                    self.circuit_breaker_open = True
                    self.circuit_breaker_opened_at = datetime.now().isoformat()
                    logger.error(f"Circuit breaker OPENED after {self.consecutive_failures} consecutive failures - semantic similarity disabled, falling back to fuzzy-only matching")
                    return None
                
                # If this is not the last attempt, wait with exponential backoff
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    logger.warning(f"Embedding API error (attempt {attempt + 1}/{self.max_retries}): {e} - Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # Last attempt failed
                    logger.error(f"Embedding API failed after {self.max_retries} attempts: {e}")
                    self._log_embedding_failure(text, str(e))
                    
                    # Raise exception on final failure
                    raise EmbeddingError(
                        f"Failed to generate embedding after {self.max_retries} attempts: {e}"
                    )
        
        # Should never reach here, but just in case
        return None
    
    def _log_embedding_failure(self, text: str, error_message: str):
        """
        Log embedding failure for debugging
        
        Args:
            text: Text that failed to embed
            error_message: Error message
        """
        # Truncate text for logging
        text_preview = text[:100] + "..." if len(text) > 100 else text
        
        logger.error(f"Embedding failure - Text: '{text_preview}', Error: {error_message}, Consecutive failures: {self.consecutive_failures}")
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity (0.0-1.0)
        """
        if len(vec1) != len(vec2):
            return 0.0
        
        # Dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Magnitudes
        mag1 = sum(a * a for a in vec1) ** 0.5
        mag2 = sum(b * b for b in vec2) ** 0.5
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        # Cosine similarity (normalize to 0-1 range)
        similarity = dot_product / (mag1 * mag2)
        return max(0.0, min(1.0, (similarity + 1) / 2))

    def get_cache_statistics(self) -> Dict:
        """
        Get embedding cache statistics
        
        Returns:
            Dict with cache performance metrics
        """
        total_requests = self.cache_hits + self.cache_misses
        cache_hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0.0
        
        total_db_requests = self.db_hits + self.db_misses
        db_hit_rate = (self.db_hits / total_db_requests * 100) if total_db_requests > 0 else 0.0
        
        return {
            "memory_cache_hits": self.cache_hits,
            "memory_cache_misses": self.cache_misses,
            "memory_cache_hit_rate": f"{cache_hit_rate:.1f}%",
            "db_cache_hits": self.db_hits,
            "db_cache_misses": self.db_misses,
            "db_cache_hit_rate": f"{db_hit_rate:.1f}%",
            "total_api_calls": self.cache_misses - self.db_hits,
            "circuit_breaker_open": self.circuit_breaker_open,
            "consecutive_failures": self.consecutive_failures
        }
