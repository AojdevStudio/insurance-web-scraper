"""
Caching utilities for improving performance.

This module provides caching mechanisms to reduce processing time for frequently accessed data.
"""

import os
import json
import hashlib
import pickle
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar, Union
from functools import lru_cache, wraps
import time
from datetime import datetime, timedelta
from loguru import logger

T = TypeVar('T')  # Type variable for generic caching


def generate_key(args: Tuple, kwargs: Dict) -> str:
    """
    Generate a cache key from function arguments.
    
    Args:
        args: Positional arguments
        kwargs: Keyword arguments
        
    Returns:
        A string hash key
    """
    key_parts = []
    
    # Add positional arguments
    for arg in args:
        try:
            key_parts.append(str(arg))
        except Exception:
            # If we can't convert to string, use type and id
            key_parts.append(f"{type(arg).__name__}:{id(arg)}")
    
    # Add keyword arguments (sorted to ensure consistency)
    for k in sorted(kwargs.keys()):
        try:
            key_parts.append(f"{k}:{kwargs[k]}")
        except Exception:
            # If we can't convert to string, use type and id
            key_parts.append(f"{k}:{type(kwargs[k]).__name__}:{id(kwargs[k])}")
    
    # Generate hash of the combined key parts
    key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
    return key


class DiskCache:
    """
    Disk-based caching for storing large objects or persistent data.
    """
    
    def __init__(self, cache_dir: str, ttl: Optional[int] = None):
        """
        Initialize the disk cache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl: Time-to-live in seconds for cached items (None for no expiration)
        """
        self.cache_dir = Path(cache_dir)
        self.ttl = ttl
        
        # Create the cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        logger.info(f"Initialized disk cache in {self.cache_dir}")
    
    def _get_cache_path(self, key: str) -> Path:
        """Get the file path for a cache key."""
        return self.cache_dir / f"{key}.cache"
    
    def _is_expired(self, timestamp: float) -> bool:
        """Check if a cache entry is expired based on its timestamp."""
        if self.ttl is None:
            return False
        
        return time.time() - timestamp > self.ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            logger.debug(f"Cache miss for key {key}")
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                timestamp, value = pickle.load(f)
            
            if self._is_expired(timestamp):
                logger.debug(f"Cache expired for key {key}")
                return None
            
            logger.debug(f"Cache hit for key {key}")
            return value
        except Exception as e:
            logger.warning(f"Error reading cache for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump((time.time(), value), f)
            
            logger.debug(f"Cached value for key {key}")
        except Exception as e:
            logger.warning(f"Error writing cache for key {key}: {e}")
    
    def clear(self, key: Optional[str] = None) -> None:
        """
        Clear cache entries.
        
        Args:
            key: Specific key to clear (if None, clears all)
        """
        if key:
            cache_path = self._get_cache_path(key)
            if cache_path.exists():
                os.remove(cache_path)
                logger.debug(f"Cleared cache for key {key}")
        else:
            # Clear all cache files
            for path in self.cache_dir.glob("*.cache"):
                os.remove(path)
            
            logger.info("Cleared all cache entries")
    
    def cleanup_expired(self) -> int:
        """
        Clean up expired cache entries.
        
        Returns:
            Number of entries removed
        """
        if self.ttl is None:
            return 0
        
        count = 0
        for path in self.cache_dir.glob("*.cache"):
            try:
                with open(path, 'rb') as f:
                    timestamp, _ = pickle.load(f)
                
                if self._is_expired(timestamp):
                    os.remove(path)
                    count += 1
            except Exception:
                # If we can't read the file, just remove it
                os.remove(path)
                count += 1
        
        logger.info(f"Removed {count} expired cache entries")
        return count


def disk_cache(cache_dir: str, ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """
    Decorator for caching function results to disk.
    
    Args:
        cache_dir: Directory to store cache files
        ttl: Time-to-live in seconds (None for no expiration)
        key_func: Custom function to generate cache keys (if None, uses arguments)
        
    Returns:
        Decorated function with disk caching
    """
    cache = DiskCache(cache_dir, ttl)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = generate_key(args, kwargs)
            
            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Not in cache, call the function
            result = func(*args, **kwargs)
            
            # Cache the result
            cache.set(key, result)
            
            return result
        
        return wrapper
    
    return decorator


class MemoryCache:
    """
    In-memory cache with LRU eviction policy.
    """
    
    def __init__(self, maxsize: int = 128, ttl: Optional[int] = None):
        """
        Initialize the memory cache.
        
        Args:
            maxsize: Maximum number of entries to keep in cache
            ttl: Time-to-live in seconds (None for no expiration)
        """
        self.maxsize = maxsize
        self.ttl = ttl
        self.cache: Dict[str, Tuple[float, Any]] = {}
        self.access_times: Dict[str, float] = {}
        
        logger.info(f"Initialized memory cache with maxsize={maxsize}, ttl={ttl}s")
    
    def _is_expired(self, timestamp: float) -> bool:
        """Check if a cache entry is expired based on its timestamp."""
        if self.ttl is None:
            return False
        
        return time.time() - timestamp > self.ttl
    
    def _evict_if_needed(self) -> None:
        """Evict the least recently used entry if the cache is full."""
        if len(self.cache) >= self.maxsize:
            # Find the least recently used key
            lru_key = min(self.access_times, key=self.access_times.get)
            
            # Remove it
            del self.cache[lru_key]
            del self.access_times[lru_key]
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if key not in self.cache:
            logger.debug(f"Cache miss for key {key}")
            return None
        
        timestamp, value = self.cache[key]
        
        if self._is_expired(timestamp):
            # Remove expired entry
            del self.cache[key]
            del self.access_times[key]
            logger.debug(f"Cache expired for key {key}")
            return None
        
        # Update access time
        self.access_times[key] = time.time()
        
        logger.debug(f"Cache hit for key {key}")
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self._evict_if_needed()
        
        now = time.time()
        self.cache[key] = (now, value)
        self.access_times[key] = now
        
        logger.debug(f"Cached value for key {key}")
    
    def clear(self, key: Optional[str] = None) -> None:
        """
        Clear cache entries.
        
        Args:
            key: Specific key to clear (if None, clears all)
        """
        if key:
            if key in self.cache:
                del self.cache[key]
                del self.access_times[key]
                logger.debug(f"Cleared cache for key {key}")
        else:
            self.cache.clear()
            self.access_times.clear()
            logger.info("Cleared all cache entries")
    
    def cleanup_expired(self) -> int:
        """
        Clean up expired cache entries.
        
        Returns:
            Number of entries removed
        """
        if self.ttl is None:
            return 0
        
        now = time.time()
        expired_keys = []
        
        for key, (timestamp, _) in self.cache.items():
            if now - timestamp > self.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            del self.access_times[key]
        
        if expired_keys:
            logger.info(f"Removed {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)


def memory_cache(maxsize: int = 128, ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """
    Decorator for caching function results in memory.
    
    Args:
        maxsize: Maximum number of entries to keep in cache
        ttl: Time-to-live in seconds (None for no expiration)
        key_func: Custom function to generate cache keys (if None, uses arguments)
        
    Returns:
        Decorated function with memory caching
    """
    cache = MemoryCache(maxsize, ttl)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = generate_key(args, kwargs)
            
            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Not in cache, call the function
            result = func(*args, **kwargs)
            
            # Cache the result
            cache.set(key, result)
            
            return result
        
        return wrapper
    
    return decorator


# Create a generic cached property decorator
class cached_property:
    """
    Decorator that converts a method into a property whose value is cached.
    
    The cached value is invalidated whenever a new value is set.
    """
    
    def __init__(self, func):
        self.func = func
        self.__doc__ = func.__doc__
        self.name = func.__name__
    
    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        
        # Create cache if it doesn't exist
        if not hasattr(instance, '_property_cache'):
            instance._property_cache = {}
        
        cache = instance._property_cache
        
        # Check if value is already cached
        if self.name not in cache:
            cache[self.name] = self.func(instance)
        
        return cache[self.name]
    
    def __set__(self, instance, value):
        # Create cache if it doesn't exist
        if not hasattr(instance, '_property_cache'):
            instance._property_cache = {}
        
        # Set the cached value
        instance._property_cache[self.name] = value
    
    def __delete__(self, instance):
        # Delete the cached value if it exists
        if hasattr(instance, '_property_cache') and self.name in instance._property_cache:
            del instance._property_cache[self.name] 