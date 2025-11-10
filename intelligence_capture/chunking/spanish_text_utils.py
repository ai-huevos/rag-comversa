"""
Utilidades de procesamiento de texto en español

Herramientas de NLP español para:
- Eliminación de stopwords
- Stemming con Snowball
- Extracción de características del español
"""

from typing import Set, List, Dict, Any
from nltk.stem.snowball import SnowballStemmer


class SpanishTextUtils:
    """
    Utilidades de NLP español para procesamiento de texto

    Proporciona:
    - Stopwords del español
    - Stemming con algoritmo Snowball
    - Extracción de características específicas del español
    """

    def __init__(self):
        """Inicializar stemmer y stopwords del español"""
        self.stemmer = SnowballStemmer('spanish')

        # Stopwords comunes del español
        # Lista expandida basada en corpus español
        self.stopwords: Set[str] = {
            'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se',
            'no', 'haber', 'por', 'con', 'su', 'para', 'como', 'estar',
            'tener', 'le', 'lo', 'todo', 'pero', 'más', 'hacer', 'o',
            'poder', 'decir', 'este', 'ir', 'otro', 'ese', 'si',
            'me', 'ya', 'ver', 'porque', 'dar', 'cuando', 'él', 'muy',
            'sin', 'vez', 'mucho', 'saber', 'qué', 'sobre', 'mi', 'alguno',
            'mismo', 'yo', 'también', 'hasta', 'año', 'dos', 'querer',
            'entre', 'así', 'primero', 'desde', 'grande', 'eso', 'ni',
            'nos', 'llegar', 'pasar', 'tiempo', 'ella', 'sí', 'día',
            'uno', 'bien', 'poco', 'deber', 'entonces', 'poner', 'cosa',
            'tanto', 'hombre', 'parecer', 'nuestro', 'tan', 'donde',
            'ahora', 'parte', 'después', 'vida', 'quedar', 'siempre',
            'creer', 'hablar', 'llevar', 'dejar', 'nada', 'cada', 'seguir',
            'menos', 'nuevo', 'encontrar', 'algo', 'solo', 'decía', 'estos',
            'trabajar', 'esa', 'mediante', 'pueden', 'país', 'mayor',
            'tal', 'ante', 'ellos', 'había', 'esas', 'estaba', 'nunca'
        }

    def remove_stopwords(self, text: str) -> str:
        """
        Eliminar stopwords del español

        Args:
            text: Texto en español

        Returns:
            Texto sin stopwords
        """
        words = text.lower().split()
        filtered = [w for w in words if w not in self.stopwords]
        return ' '.join(filtered)

    def stem_text(self, text: str) -> List[str]:
        """
        Aplicar stemming español

        Args:
            text: Texto en español

        Returns:
            Lista de stems (raíces de palabras)
        """
        words = text.lower().split()
        return [self.stemmer.stem(w) for w in words if w]

    def extract_features(self, text: str) -> Dict[str, Any]:
        """
        Extraer características del texto en español

        Analiza:
        - Densidad de stopwords
        - Diversidad léxica (stems únicos)
        - Uso de acentos y caracteres especiales
        - Longitud promedio de palabras

        Args:
            text: Texto en español

        Returns:
            Diccionario con características del texto
        """
        words = text.lower().split()

        if not words:
            return {
                'total_words': 0,
                'stopword_count': 0,
                'stopword_ratio': 0.0,
                'unique_stems': 0,
                'has_accents': False,
                'avg_word_length': 0.0,
                'lexical_diversity': 0.0
            }

        stopword_count = sum(1 for w in words if w in self.stopwords)
        stems = self.stem_text(text)
        unique_stems = set(stems)

        # Detectar acentos y caracteres especiales del español
        spanish_chars = 'áéíóúñüÁÉÍÓÚÑÜ¿¡'
        has_accents = any(c in spanish_chars for c in text)

        # Calcular diversidad léxica (stems únicos / total palabras)
        lexical_diversity = len(unique_stems) / len(words) if words else 0.0

        return {
            'total_words': len(words),
            'stopword_count': stopword_count,
            'stopword_ratio': stopword_count / len(words),
            'unique_stems': len(unique_stems),
            'has_accents': has_accents,
            'avg_word_length': sum(len(w) for w in words) / len(words),
            'lexical_diversity': lexical_diversity
        }

    def is_spanish(self, text: str, threshold: float = 0.3) -> bool:
        """
        Detectar si el texto es español

        Usa heurística de stopwords: si >30% son stopwords españolas,
        probablemente es español

        Args:
            text: Texto a analizar
            threshold: Umbral de ratio de stopwords (default: 0.3)

        Returns:
            True si probablemente es español
        """
        features = self.extract_features(text)

        # Criterios: ratio de stopwords alto O presencia de acentos
        return (
            features['stopword_ratio'] > threshold or
            features['has_accents']
        )
