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
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher
import json

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
    
    def __init__(self, config: Dict, openai_api_key: Optional[str] = None):
        """
        Initialize duplicate detector
        
        Args:
            config: Configuration dict with similarity_thresholds and similarity_weights
            openai_api_key: Optional OpenAI API key for semantic similarity
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
        
        # Embedding cache
        self.embedding_cache = {} if self.enable_caching else None
        
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
        Find duplicate entities using fuzzy + semantic matching
        
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
        
        # Calculate similarity for each existing entity
        candidates = []
        for existing in existing_entities:
            existing_text = self._get_entity_text(existing, entity_type)
            if not existing_text:
                continue
            
            # Calculate combined similarity score
            similarity = self._calculate_combined_similarity(
                entity_text,
                existing_text,
                entity_type
            )
            
            # Only include if above threshold
            if similarity >= threshold:
                candidates.append((existing, similarity))
        
        # Sort by similarity (highest first) and limit to max_candidates
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:self.max_candidates]
    
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
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0.0-1.0), or 0.0 if OpenAI not available
        """
        if not self.openai_client or not text1 or not text2:
            return 0.0
        
        try:
            # Get embeddings (with caching)
            emb1 = self._get_embedding(text1)
            emb2 = self._get_embedding(text2)
            
            if emb1 is None or emb2 is None:
                return 0.0
            
            # Calculate cosine similarity
            return self._cosine_similarity(emb1, emb2)
            
        except Exception as e:
            print(f"  ⚠️  Semantic similarity error: {e}")
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
        
        Args:
            entity: Entity dict
            entity_type: Type of entity
            
        Returns:
            Text to use for similarity comparison
        """
        # Try common field names
        if "name" in entity and entity["name"]:
            return str(entity["name"])
        elif "description" in entity and entity["description"]:
            return str(entity["description"])
        elif "title" in entity and entity["title"]:
            return str(entity["title"])
        
        # Entity-specific fields
        if entity_type == "pain_points" and "type" in entity:
            return str(entity["type"])
        
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
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding for text (with caching)
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if error
        """
        # Check cache first
        if self.enable_caching and text in self.embedding_cache:
            return self.embedding_cache[text]
        
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            embedding = response.data[0].embedding
            
            # Cache for future use
            if self.enable_caching:
                self.embedding_cache[text] = embedding
            
            return embedding
            
        except Exception as e:
            print(f"  ⚠️  Embedding error: {e}")
            return None
    
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
