"""
Performance monitoring and profiling utilities.

This module provides tools for monitoring performance metrics and identifying bottlenecks.
"""

import time
import os
import psutil
import cProfile
import pstats
import io
import tracemalloc
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union
from pathlib import Path
import json
from loguru import logger


class PerformanceProfiler:
    """
    Utility for profiling Python code to identify performance bottlenecks.
    """
    
    def __init__(self, enabled: bool = True, output_dir: Optional[str] = None):
        """
        Initialize the performance profiler.
        
        Args:
            enabled: Whether profiling is enabled
            output_dir: Directory to save profile results
        """
        self.enabled = enabled
        self.output_dir = output_dir or os.path.join(os.getcwd(), "profiles")
        self.profiler = None
        
        if self.output_dir:
            os.makedirs(self.output_dir, exist_ok=True)
    
    def profile_function(self, func: Callable) -> Callable:
        """
        Decorator to profile a function.
        
        Args:
            func: Function to profile
            
        Returns:
            Wrapped function that will be profiled when called
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.enabled:
                return func(*args, **kwargs)
            
            profiler = cProfile.Profile()
            profiler.enable()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                profiler.disable()
                
                # Create a string buffer to capture the profile output
                s = io.StringIO()
                ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
                ps.print_stats(20)  # Print top 20 time-consuming functions
                
                # Save to file if output directory is set
                if self.output_dir:
                    timestamp = time.strftime("%Y%m%d-%H%M%S")
                    output_path = os.path.join(self.output_dir, f"{func.__name__}_{timestamp}.prof")
                    
                    ps.dump_stats(output_path)
                    logger.info(f"Profile saved to {output_path}")
                
                # Log the profile summary
                logger.debug("Profile results for {}:\n{}".format(func.__name__, s.getvalue()))
        
        return wrapper
    
    def profile_block(self, name: str = "code_block"):
        """
        Context manager for profiling a block of code.
        
        Args:
            name: Name to identify this profiling block
            
        Returns:
            Context manager that profiles the code block
        """
        class ProfileContext:
            def __init__(self, profiler, name):
                self.profiler = profiler
                self.name = name
                self.prof = cProfile.Profile()
            
            def __enter__(self):
                if self.profiler.enabled:
                    self.prof.enable()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if not self.profiler.enabled:
                    return
                
                self.prof.disable()
                
                # Create a string buffer to capture the profile output
                s = io.StringIO()
                ps = pstats.Stats(self.prof, stream=s).sort_stats('cumulative')
                ps.print_stats(20)  # Print top 20 time-consuming functions
                
                # Save to file if output directory is set
                if self.profiler.output_dir:
                    timestamp = time.strftime("%Y%m%d-%H%M%S")
                    output_path = os.path.join(self.profiler.output_dir, f"{self.name}_{timestamp}.prof")
                    
                    ps.dump_stats(output_path)
                    logger.info(f"Profile saved to {output_path}")
                
                # Log the profile summary
                logger.debug("Profile results for {}:\n{}".format(self.name, s.getvalue()))
        
        return ProfileContext(self, name)


class MemoryProfiler:
    """
    Utility for profiling memory usage to identify memory leaks and inefficiencies.
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize the memory profiler.
        
        Args:
            enabled: Whether memory profiling is enabled
        """
        self.enabled = enabled
        self.snapshot = None
    
    def start(self):
        """Start memory tracking."""
        if self.enabled:
            tracemalloc.start()
            self.snapshot = None
    
    def take_snapshot(self):
        """Take a snapshot of current memory allocation."""
        if self.enabled:
            self.snapshot = tracemalloc.take_snapshot()
            return self.snapshot
        return None
    
    def compare_to_snapshot(self, top_n: int = 10):
        """
        Compare current memory usage to the previous snapshot.
        
        Args:
            top_n: Number of top memory blocks to display
            
        Returns:
            Statistics comparing memory usage
        """
        if not self.enabled or self.snapshot is None:
            return None
        
        current = tracemalloc.take_snapshot()
        stats = current.compare_to(self.snapshot, 'lineno')
        
        result = []
        for stat in stats[:top_n]:
            result.append({
                'current_size': stat.size_diff,
                'current_count': stat.count_diff,
                'traceback': str(stat.traceback)
            })
        
        return result
    
    def display_top_stats(self, snapshot=None, top_n: int = 10):
        """
        Display top memory allocations.
        
        Args:
            snapshot: Memory snapshot to analyze (if None, takes a new one)
            top_n: Number of top allocations to display
            
        Returns:
            Top memory allocations
        """
        if not self.enabled:
            return None
        
        if snapshot is None:
            snapshot = tracemalloc.take_snapshot()
        
        stats = snapshot.statistics('lineno')
        
        result = []
        for stat in stats[:top_n]:
            result.append({
                'size': stat.size,
                'count': stat.count,
                'traceback': str(stat.traceback)
            })
        
        return result
    
    def stop(self):
        """Stop memory tracking."""
        if self.enabled:
            tracemalloc.stop()


class PerformanceMonitor:
    """
    Utility for monitoring performance metrics such as execution time and memory usage.
    """
    
    def __init__(self, track_memory: bool = True):
        """
        Initialize the performance monitor.
        
        Args:
            track_memory: Whether to track memory usage
        """
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.metrics = {}
        self.track_memory = track_memory
    
    def start(self):
        """Start monitoring performance."""
        self.start_time = time.time()
        
        if self.track_memory:
            self.start_memory = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)  # MB
    
    def stop(self):
        """Stop monitoring performance and calculate metrics."""
        self.end_time = time.time()
        
        metrics = {
            "execution_time": self.end_time - self.start_time,
        }
        
        if self.track_memory:
            self.end_memory = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)  # MB
            metrics.update({
                "memory_used": self.end_memory - self.start_memory,
                "peak_memory": self.end_memory,
            })
        
        self.metrics = metrics
        return metrics
    
    def log_metrics(self, operation: str):
        """Log performance metrics."""
        logger.info(f"Performance metrics for {operation}:")
        logger.info(f"Execution time: {self.metrics['execution_time']:.2f} seconds")
        
        if self.track_memory:
            logger.info(f"Memory used: {self.metrics['memory_used']:.2f} MB")
            logger.info(f"Peak memory: {self.metrics['peak_memory']:.2f} MB")
    
    def record_to_file(self, operation: str, output_dir: str = None):
        """
        Record performance metrics to a JSON file.
        
        Args:
            operation: Name of the operation
            output_dir: Directory to save the metrics file
        """
        if output_dir is None:
            output_dir = os.path.join(os.getcwd(), "performance_logs")
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{operation}_{timestamp}.json"
        
        with open(os.path.join(output_dir, filename), 'w') as f:
            json.dump({
                "operation": operation,
                "timestamp": timestamp,
                "metrics": self.metrics
            }, f, indent=4)


def time_it(func: Callable) -> Callable:
    """
    Decorator to measure execution time of a function.
    
    Args:
        func: Function to measure
        
    Returns:
        Wrapped function that logs execution time
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logger.debug(f"{func.__name__} executed in {end_time - start_time:.2f} seconds")
        return result
    
    return wrapper 