"""
Domain Detector - Generic, configuration-driven domain detection

This module determines if a question has verifiable ground truth
and which domain it belongs to (e.g., taj_hotels_pricing, restaurant_menus, etc.)

The detector is GENERIC and CONFIGURABLE - it fetches domain metadata
from the Ground Truth Service and uses that to detect domains.
"""

import re
import logging
import httpx
from typing import Optional, Tuple, List, Dict, Any

logger = logging.getLogger(__name__)


class DomainDetector:
    """
    Generic, configuration-driven domain detector.

    Fetches domain metadata from Ground Truth Service and uses
    detection rules (keywords, patterns) to identify domains.

    This is fully extensible - adding a new domain requires NO code changes,
    just adding domain metadata to the Ground Truth Service.
    """

    def __init__(self, ground_truth_service_url: str):
        """
        Initialize domain detector.

        Args:
            ground_truth_service_url: URL of Ground Truth Service
        """
        self.ground_truth_service_url = ground_truth_service_url
        self.http_client = httpx.Client(
            base_url=ground_truth_service_url,
            timeout=10.0
        )

        # Cache of domain metadata
        self.domains_cache: Dict[str, Dict[str, Any]] = {}

        # Load domain metadata on initialization
        self._load_domains()

    def _load_domains(self):
        """
        Load domain metadata from Ground Truth Service.

        Fetches all domains and caches their metadata (keywords, patterns, etc.)
        """
        try:
            response = self.http_client.get("/domains")
            response.raise_for_status()

            domains = response.json()

            for domain in domains:
                domain_name = domain["name"]
                extra_metadata = domain.get("extra_metadata", {})

                self.domains_cache[domain_name] = {
                    "value_type": domain["value_type"],
                    "keywords": extra_metadata.get("detection_keywords", []),
                    "entity_patterns": extra_metadata.get("entity_patterns", []),
                    "metadata": extra_metadata
                }

                logger.info(f"Loaded domain: {domain_name} (type: {domain['value_type']})")

            logger.info(f"Loaded {len(self.domains_cache)} domains from Ground Truth Service")

        except Exception as e:
            logger.error(f"Error loading domains: {e}")
            # Continue with empty cache - worker will skip reward computation

    def detect_domain(self, question: str, answer: str = "") -> Optional[Tuple[str, str]]:
        """
        Detect which domain this question belongs to.

        Uses domain metadata from Ground Truth Service to detect domains.
        This is GENERIC - no hardcoded patterns!

        Args:
            question: User's question
            answer: Generated answer (optional, used for better detection)

        Returns:
            Tuple of (domain_name, entity_key) or None if no domain detected

        Examples:
            ("taj_hotels_pricing", "taj mahal palace")
            ("restaurant_menus", "taj_restaurant_xyz")
            None
        """
        # Combine question and answer for better matching
        text = (question + " " + answer).lower()

        # Try each domain in cache
        for domain_name, domain_config in self.domains_cache.items():
            result = self._detect_domain_generic(text, domain_name, domain_config)
            if result:
                return result

        return None

    def _detect_domain_generic(
        self,
        text: str,
        domain_name: str,
        domain_config: Dict[str, Any]
    ) -> Optional[Tuple[str, str]]:
        """
        Generic domain detection using configuration.

        Args:
            text: Combined question + answer text (lowercase)
            domain_name: Domain name (e.g., "taj_hotels_pricing")
            domain_config: Domain configuration with keywords and patterns

        Returns:
            Tuple of (domain_name, entity_key) or None
        """
        # Check if any detection keywords are present
        keywords = domain_config.get("keywords", [])
        if keywords and not any(keyword.lower() in text for keyword in keywords):
            return None

        # Try to extract entity using patterns
        entity_patterns = domain_config.get("entity_patterns", [])
        for pattern in entity_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entity_name = match.group(0).strip()
                # Normalize entity name
                entity_key = self._normalize_entity_name(entity_name, domain_name)
                logger.info(f"Detected domain: {domain_name}, entity: {entity_key}")
                return (domain_name, entity_key)

        return None

    def _normalize_entity_name(self, entity_name: str, domain_name: str) -> str:
        """
        Normalize entity name to match ground truth keys.

        This is generic - it just normalizes whitespace and lowercases.
        Domain-specific normalization can be added via aliases in Ground Truth Service.

        Args:
            entity_name: Raw entity name from text
            domain_name: Domain name (for domain-specific normalization if needed)

        Returns:
            Normalized entity key
        """
        # Convert to lowercase and normalize whitespace
        normalized = re.sub(r'\s+', ' ', entity_name.lower().strip())

        return normalized


