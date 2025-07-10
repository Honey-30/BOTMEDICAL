"""
Caching utilities for the healthcare chatbot.
"""

import json
import pickle
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List, Callable
from functools import wraps
import redis
from flask import current_app, request, g

# Configure logging
logger = logging.getLogger(__name__)

class CacheManager:
    """Centralized cache management for the application."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.redis_client = None
        self.local_cache = {}  # Fallback local cache
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
        
        # Initialize Redis connection
        self._init_redis()
        
        # Cache configuration
        self.default_timeout = self.config.get('default_timeout', 300)  # 5 minutes
        self.max_local_cache_size = self.config.get('max_local_cache_size', 1000)
        
        # Cache key prefixes
        self.key_prefixes = {
            'user_session': 'user_session:',
            'symptom_analysis': 'symptom_analysis:',
            'model_prediction': 'model_prediction:',
            'nlp_result': 'nlp_result:',
            'api_response': 'api_response:',
            'user_profile': 'user_profile:',
            'health_report': 'health_report:'
        }
    
    def _init_redis(self):
        """Initialize Redis connection."""
        try:
            redis_url = self.config.get('redis_url', 'redis://localhost:6379/2')
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache connection established")
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using local cache only.")
            self.redis_client = None
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        # Create a deterministic key from arguments
        key_data = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_data += f":{':'.join(f'{k}={v}' for k, v in sorted_kwargs)}"
        
        # Hash the key if it's too long
        if len(key_data) > 200:
            key_hash = hashlib.md5(key_data.encode()).hexdigest()
            return f"{prefix}:hash:{key_hash}"
        
        return key_data
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        try:
            # Try Redis first
            if self.redis_client:
                try:
                    value = self.redis_client.get(key)
                    if value is not None:
                        self.cache_stats['hits'] += 1
                        return json.loads(value)
                except (redis.RedisError, json.JSONDecodeError) as e:
                    logger.warning(f"Redis get error: {e}")
            
            # Fallback to local cache
            if key in self.local_cache:
                cache_entry = self.local_cache[key]
                if cache_entry['expires'] > datetime.utcnow():
                    self.cache_stats['hits'] += 1
                    return cache_entry['value']
                else:
                    # Expired entry
                    del self.local_cache[key]
            
            self.cache_stats['misses'] += 1
            return default
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return default
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """Set value in cache."""
        if timeout is None:
            timeout = self.default_timeout
        
        try:
            # Try Redis first
            if self.redis_client:
                try:
                    serialized_value = json.dumps(value, default=str)
                    self.redis_client.setex(key, timeout, serialized_value)
                    self.cache_stats['sets'] += 1
                    return True
                except (redis.RedisError, json.JSONEncodeError) as e:
                    logger.warning(f"Redis set error: {e}")
            
            # Fallback to local cache
            # Clean up local cache if it's too large
            if len(self.local_cache) >= self.max_local_cache_size:
                self._cleanup_local_cache()
            
            expires = datetime.utcnow() + timedelta(seconds=timeout)
            self.local_cache[key] = {
                'value': value,
                'expires': expires
            }
            
            self.cache_stats['sets'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            deleted = False
            
            # Delete from Redis
            if self.redis_client:
                try:
                    result = self.redis_client.delete(key)
                    deleted = result > 0
                except redis.RedisError as e:
                    logger.warning(f"Redis delete error: {e}")
            
            # Delete from local cache
            if key in self.local_cache:
                del self.local_cache[key]
                deleted = True
            
            if deleted:
                self.cache_stats['deletes'] += 1
            
            return deleted
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        try:
            deleted_count = 0
            
            # Delete from Redis
            if self.redis_client:
                try:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        deleted_count += self.redis_client.delete(*keys)
                except redis.RedisError as e:
                    logger.warning(f"Redis pattern delete error: {e}")
            
            # Delete from local cache
            import fnmatch
            local_keys_to_delete = [
                key for key in self.local_cache.keys()
                if fnmatch.fnmatch(key, pattern)
            ]
            
            for key in local_keys_to_delete:
                del self.local_cache[key]
                deleted_count += 1
            
            self.cache_stats['deletes'] += deleted_count
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cache pattern delete error: {e}")
            return 0
    
    def _cleanup_local_cache(self):
        """Clean up expired entries from local cache."""
        current_time = datetime.utcnow()
        expired_keys = [
            key for key, entry in self.local_cache.items()
            if entry['expires'] <= current_time
        ]
        
        for key in expired_keys:
            del self.local_cache[key]
        
        # If still too large, remove oldest entries
        if len(self.local_cache) >= self.max_local_cache_size:
            # Sort by expiration time and remove oldest
            sorted_entries = sorted(
                self.local_cache.items(),
                key=lambda x: x[1]['expires']
            )
            
            remove_count = len(self.local_cache) - self.max_local_cache_size + 100
            for key, _ in sorted_entries[:remove_count]:
                del self.local_cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            'hit_rate': hit_rate,
            'total_requests': total_requests,
            'redis_connected': self.redis_client is not None,
            'local_cache_size': len(self.local_cache),
            **self.cache_stats
        }
        
        # Add Redis info if available
        if self.redis_client:
            try:
                redis_info = self.redis_client.info('memory')
                stats['redis_memory_used'] = redis_info.get('used_memory_human', 'N/A')
                stats['redis_memory_peak'] = redis_info.get('used_memory_peak_human', 'N/A')
            except redis.RedisError:
                pass
        
        return stats

# Global cache manager instance
cache_manager = CacheManager()

def cached(timeout: int = 300, key_prefix: str = 'default'):
    """
    Decorator for caching function results.
    
    Args:
        timeout: Cache timeout in seconds
        key_prefix: Prefix for cache keys
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager._generate_cache_key(
                key_prefix, f.__name__, *args, **kwargs
            )
            
            # Try to get from cache
            result = cache_manager.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            cache_manager.set(cache_key, result, timeout)
            
            return result
        
        return wrapper
    return decorator

def cache_response(key: str, data: Any, timeout: int = 300) -> bool:
    """Cache API response data."""
    return cache_manager.set(key, data, timeout)

def get_cached_response(key: str) -> Optional[Any]:
    """Get cached API response data."""
    return cache_manager.get(key)

def invalidate_user_cache(user_id: str):
    """Invalidate all cache entries for a specific user."""
    patterns = [
        f"user_session:{user_id}:*",
        f"symptom_analysis:{user_id}:*",
        f"user_profile:{user_id}:*",
        f"health_report:{user_id}:*"
    ]
    
    for pattern in patterns:
        cache_manager.delete_pattern(pattern)

def cache_user_session(user_id: str, session_data: Dict[str, Any], timeout: int = 3600):
    """Cache user session data."""
    key = f"{cache_manager.key_prefixes['user_session']}{user_id}"
    return cache_manager.set(key, session_data, timeout)

def get_cached_user_session(user_id: str) -> Optional[Dict[str, Any]]:
    """Get cached user session data."""
    key = f"{cache_manager.key_prefixes['user_session']}{user_id}"
    return cache_manager.get(key)

def cache_symptom_analysis(
    user_id: str, 
    symptoms: List[str], 
    analysis_result: Dict[str, Any],
    timeout: int = 1800
) -> bool:
    """Cache symptom analysis results."""
    # Create a hash of symptoms for the key
    symptoms_hash = hashlib.md5('|'.join(sorted(symptoms)).encode()).hexdigest()
    key = f"{cache_manager.key_prefixes['symptom_analysis']}{user_id}:{symptoms_hash}"
    
    return cache_manager.set(key, analysis_result, timeout)

def get_cached_symptom_analysis(user_id: str, symptoms: List[str]) -> Optional[Dict[str, Any]]:
    """Get cached symptom analysis results."""
    symptoms_hash = hashlib.md5('|'.join(sorted(symptoms)).encode()).hexdigest()
    key = f"{cache_manager.key_prefixes['symptom_analysis']}{user_id}:{symptoms_hash}"
    
    return cache_manager.get(key)

def cache_model_prediction(
    model_name: str,
    input_hash: str,
    prediction_result: Any,
    timeout: int = 900
) -> bool:
    """Cache ML model predictions."""
    key = f"{cache_manager.key_prefixes['model_prediction']}{model_name}:{input_hash}"
    return cache_manager.set(key, prediction_result, timeout)

def get_cached_model_prediction(model_name: str, input_hash: str) -> Optional[Any]:
    """Get cached ML model predictions."""
    key = f"{cache_manager.key_prefixes['model_prediction']}{model_name}:{input_hash}"
    return cache_manager.get(key)

def cache_nlp_result(
    text_hash: str,
    nlp_result: Dict[str, Any],
    timeout: int = 1800
) -> bool:
    """Cache NLP processing results."""
    key = f"{cache_manager.key_prefixes['nlp_result']}{text_hash}"
    return cache_manager.set(key, nlp_result, timeout)

def get_cached_nlp_result(text_hash: str) -> Optional[Dict[str, Any]]:
    """Get cached NLP processing results."""
    key = f"{cache_manager.key_prefixes['nlp_result']}{text_hash}"
    return cache_manager.get(key)

class CacheWarmer:
    """Utility class for warming up caches with commonly used data."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
    
    def warm_symptom_vocabulary(self, vocabulary: Dict[str, Any]):
        """Warm cache with symptom vocabulary."""
        key = "symptom_vocabulary:all"
        self.cache_manager.set(key, vocabulary, timeout=86400)  # 24 hours
    
    def warm_disease_knowledge(self, knowledge: Dict[str, Any]):
        """Warm cache with disease knowledge base."""
        key = "disease_knowledge:all"
        self.cache_manager.set(key, knowledge, timeout=86400)  # 24 hours
    
    def warm_common_predictions(self, predictions: List[Dict[str, Any]]):
        """Warm cache with common disease predictions."""
        key = "common_predictions:all"
        self.cache_manager.set(key, predictions, timeout=3600)  # 1 hour

def create_cache_key(*args, **kwargs) -> str:
    """Create a deterministic cache key from arguments."""
    return cache_manager._generate_cache_key('custom', *args, **kwargs)

def clear_all_cache():
    """Clear all cache entries (use with caution)."""
    try:
        if cache_manager.redis_client:
            cache_manager.redis_client.flushdb()
        
        cache_manager.local_cache.clear()
        
        logger.info("All cache entries cleared")
        return True
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return False

def get_cache_info() -> Dict[str, Any]:
    """Get comprehensive cache information."""
    return {
        'cache_stats': cache_manager.get_stats(),
        'redis_connected': cache_manager.redis_client is not None,
        'local_cache_entries': len(cache_manager.local_cache),
        'cache_prefixes': list(cache_manager.key_prefixes.keys())
    }

class SmartCache:
    """Smart caching with automatic invalidation and refresh."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.refresh_callbacks = {}
    
    def smart_get(
        self, 
        key: str, 
        refresh_callback: Callable,
        timeout: int = 300,
        refresh_threshold: float = 0.8
    ) -> Any:
        """
        Smart cache get with automatic refresh.
        
        Args:
            key: Cache key
            refresh_callback: Function to call for refresh
            timeout: Cache timeout
            refresh_threshold: Refresh when this fraction of TTL remains
        """
        # Try to get from cache
        result = self.cache_manager.get(key)
        
        if result is not None:
            # Check if we need to refresh
            if self._should_refresh(key, timeout, refresh_threshold):
                try:
                    # Refresh in background (simplified - in production use task queue)
                    fresh_result = refresh_callback()
                    self.cache_manager.set(key, fresh_result, timeout)
                except Exception as e:
                    logger.warning(f"Background refresh failed for key {key}: {e}")
            
            return result
        
        # Cache miss - fetch and store
        try:
            result = refresh_callback()
            self.cache_manager.set(key, result, timeout)
            return result
        except Exception as e:
            logger.error(f"Failed to fetch data for key {key}: {e}")
            return None
    
    def _should_refresh(self, key: str, timeout: int, threshold: float) -> bool:
        """Check if cache entry should be refreshed."""
        # This is simplified - in production you'd check TTL from Redis
        # For now, randomly refresh to demonstrate the concept
        import random
        return random.random() < 0.1  # 10% chance of refresh

# Initialize smart cache
smart_cache = SmartCache(cache_manager)
