#!/usr/bin/env python3
"""
Performance Logging Module
Provides structured logging, timing measurements, and performance metrics
for better visibility into build performance
"""

import time
import threading
import psutil
import os
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class LogLevel(Enum):
    """Log level enumeration for filtering messages"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    
    @classmethod
    def from_string(cls, level_str: str) -> 'LogLevel':
        """Convert string to LogLevel"""
        level_map = {
            'DEBUG': cls.DEBUG,
            'INFO': cls.INFO,
            'WARNING': cls.WARNING,
            'WARN': cls.WARNING,
            'ERROR': cls.ERROR
        }
        return level_map.get(level_str.upper(), cls.INFO)


@dataclass
class TimingMetric:
    """Represents a timing measurement"""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def finish(self):
        """Mark the timing metric as finished"""
        if self.end_time is None:
            self.end_time = time.time()
            self.duration = self.end_time - self.start_time


@dataclass
class PerformanceStats:
    """Container for performance statistics"""
    files_processed: int = 0
    files_skipped: int = 0
    files_error: int = 0
    processing_rate: float = 0.0  # files per second
    cache_hits: int = 0
    cache_misses: int = 0
    memory_usage_mb: float = 0.0
    parallel_workers: int = 0
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage"""
        total_cache_ops = self.cache_hits + self.cache_misses
        if total_cache_ops == 0:
            return 0.0
        return (self.cache_hits / total_cache_ops) * 100
    
    @property
    def total_files(self) -> int:
        """Total files involved in processing"""
        return self.files_processed + self.files_skipped + self.files_error


class PerformanceLogger:
    """Thread-safe performance logger with configurable verbosity"""
    
    def __init__(self, log_level: LogLevel = LogLevel.INFO, quiet: bool = False, verbose: bool = False):
        self._timings: Dict[str, List[TimingMetric]] = defaultdict(list)
        self._stats: Dict[str, PerformanceStats] = defaultdict(PerformanceStats)
        self._lock = threading.RLock()
        self._build_start_time = time.time()
        self._active_timers: Dict[str, TimingMetric] = {}
        
        # Configure log level based on quiet/verbose flags
        if quiet:
            self._log_level = LogLevel.WARNING
        elif verbose:
            self._log_level = LogLevel.DEBUG
        else:
            self._log_level = log_level
        
        # Allow environment variable override
        env_level = os.environ.get('BGP_LOG_LEVEL')
        if env_level:
            self._log_level = LogLevel.from_string(env_level)
    
    def set_log_level(self, level: Union[LogLevel, str]):
        """Set the minimum log level for output"""
        if isinstance(level, str):
            self._log_level = LogLevel.from_string(level)
        else:
            self._log_level = level
    
    def set_quiet_mode(self, quiet: bool):
        """Enable/disable quiet mode (WARNING and ERROR only)"""
        if quiet:
            self._log_level = LogLevel.WARNING
        else:
            self._log_level = LogLevel.INFO
    
    def set_verbose_mode(self, verbose: bool):
        """Enable/disable verbose mode (all messages including DEBUG)"""
        if verbose:
            self._log_level = LogLevel.DEBUG
        else:
            self._log_level = LogLevel.INFO
    
    def start_timing(self, operation: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start timing an operation
        
        Args:
            operation: Name of the operation
            metadata: Optional metadata about the operation
        
        Returns:
            Timer ID for stopping the timer
        """
        with self._lock:
            timer_id = f"{operation}_{time.time()}_{threading.current_thread().ident}"
            timing = TimingMetric(
                name=operation,
                start_time=time.time(),
                metadata=metadata or {}
            )
            self._active_timers[timer_id] = timing
            return timer_id
    
    def stop_timing(self, timer_id: str) -> Optional[float]:
        """
        Stop timing an operation
        
        Args:
            timer_id: Timer ID returned by start_timing
        
        Returns:
            Duration in seconds, or None if timer not found
        """
        with self._lock:
            if timer_id in self._active_timers:
                timing = self._active_timers.pop(timer_id)
                timing.finish()
                self._timings[timing.name].append(timing)
                return timing.duration
            return None
    
    @contextmanager
    def time_operation(self, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager for timing operations
        
        Args:
            operation: Name of the operation
            metadata: Optional metadata about the operation
        """
        timer_id = self.start_timing(operation, metadata)
        try:
            yield
        finally:
            self.stop_timing(timer_id)
    
    def update_stats(self, category: str, **kwargs):
        """
        Update performance statistics for a category
        
        Args:
            category: Category name (e.g., 'image_optimization', 'file_copying')
            **kwargs: Stat values to update
        """
        with self._lock:
            stats = self._stats[category]
            for key, value in kwargs.items():
                if hasattr(stats, key):
                    if key in ['files_processed', 'files_skipped', 'files_error', 'cache_hits', 'cache_misses']:
                        # Accumulate these values
                        current_value = getattr(stats, key)
                        setattr(stats, key, current_value + value)
                    else:
                        # Set these values directly
                        setattr(stats, key, value)
    
    def log_structured(self, level: str, component: str, message: str, 
                      emoji: str = "", duration: Optional[float] = None,
                      stats: Optional[Dict[str, Any]] = None, 
                      extra: Optional[Dict[str, Any]] = None):
        """
        Log a structured message with performance data
        
        Args:
            level: Log level (INFO, DEBUG, WARN, ERROR)
            component: Component name (e.g., 'AssetManager', 'ImageOptimizer')
            message: Human-readable message
            emoji: Emoji prefix for visual appeal
            duration: Optional duration in seconds
            stats: Optional performance statistics
            extra: Optional extra metadata
        """
        # Check if message should be logged based on current log level
        message_level = LogLevel.from_string(level)
        if message_level.value < self._log_level.value:
            return  # Skip messages below current log level
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
        
        # Build the display message
        display_parts = []
        
        # Add timestamp for verbose mode or ERROR/WARNING messages
        if self._log_level == LogLevel.DEBUG or message_level in [LogLevel.ERROR, LogLevel.WARNING]:
            display_parts.append(f"[{timestamp}]")
        
        # Add log level indicator for DEBUG mode
        if self._log_level == LogLevel.DEBUG:
            display_parts.append(f"[{level:5s}]")
        
        # Add component name in DEBUG mode
        if self._log_level == LogLevel.DEBUG and component:
            display_parts.append(f"[{component}]")
        
        if emoji:
            display_parts.append(emoji)
        
        display_parts.append(message)
        
        if duration is not None:
            if duration < 1.0:
                display_parts.append(f"({duration*1000:.1f}ms)")
            else:
                display_parts.append(f"({duration:.2f}s)")
        
        if stats:
            stat_parts = []
            for key, value in stats.items():
                if key == 'processing_rate' and value > 0:
                    stat_parts.append(f"{value:.1f}/s")
                elif key in ['files_processed', 'files_skipped', 'cache_hits']:
                    stat_parts.append(f"{key.replace('_', ' ')}: {value}")
                elif key == 'memory_usage_mb' and value > 0:
                    stat_parts.append(f"mem: {value:.1f}MB")
                elif key == 'cache_hit_rate' and value > 0:
                    stat_parts.append(f"cache: {value:.1f}%")
            
            if stat_parts:
                display_parts.append(f"[{', '.join(stat_parts)}]")
        
        print(" ".join(display_parts))
    
    def log_info(self, component: str, message: str, emoji: str = "ℹ️", **kwargs):
        """Log an info message"""
        self.log_structured("INFO", component, message, emoji, **kwargs)
    
    def log_debug(self, component: str, message: str, emoji: str = "🔍", **kwargs):
        """Log a debug message"""
        self.log_structured("DEBUG", component, message, emoji, **kwargs)
    
    def log_warn(self, component: str, message: str, emoji: str = "⚠️", **kwargs):
        """Log a warning message"""
        self.log_structured("WARN", component, message, emoji, **kwargs)
    
    def log_error(self, component: str, message: str, emoji: str = "❌", **kwargs):
        """Log an error message"""
        self.log_structured("ERROR", component, message, emoji, **kwargs)
    
    def log_success(self, component: str, message: str, emoji: str = "✅", **kwargs):
        """Log a success message"""
        self.log_structured("INFO", component, message, emoji, **kwargs)
    
    def log_phase_start(self, component: str, phase: str, emoji: str = "🚀"):
        """Log the start of a build phase"""
        self.log_info(component, f"Starting {phase}...", emoji)
    
    def log_phase_complete(self, component: str, phase: str, duration: float, emoji: str = "✅", **stats):
        """Log the completion of a build phase"""
        self.log_success(component, f"{phase} completed", emoji, duration=duration, stats=stats)
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except (ImportError, psutil.NoSuchProcess):
            return 0.0
    
    def calculate_processing_rate(self, files_processed: int, duration: float) -> float:
        """Calculate processing rate in files per second"""
        if duration > 0:
            return files_processed / duration
        return 0.0
    
    def get_timing_summary(self) -> Dict[str, Any]:
        """Get a summary of all timing measurements"""
        with self._lock:
            summary = {}
            
            for operation, timings in self._timings.items():
                if not timings:
                    continue
                
                durations = [t.duration for t in timings if t.duration is not None]
                if not durations:
                    continue
                
                summary[operation] = {
                    'count': len(durations),
                    'total_time': sum(durations),
                    'avg_time': sum(durations) / len(durations),
                    'min_time': min(durations),
                    'max_time': max(durations)
                }
            
            return summary
    
    def get_stats_summary(self) -> Dict[str, PerformanceStats]:
        """Get a summary of all performance statistics"""
        with self._lock:
            return dict(self._stats)
    
    def print_build_summary(self):
        """Print a comprehensive build performance summary"""
        with self._lock:
            total_build_time = time.time() - self._build_start_time
            
            print(f"\n{'='*60}")
            print(f"🎯 BUILD PERFORMANCE SUMMARY")
            print(f"{'='*60}")
            
            # Overall build time
            if total_build_time < 60:
                print(f"⏱️  Total Build Time: {total_build_time:.2f}s")
            else:
                minutes = int(total_build_time // 60)
                seconds = total_build_time % 60
                print(f"⏱️  Total Build Time: {minutes}m {seconds:.1f}s")
            
            # Memory usage
            memory_usage = self.get_memory_usage()
            if memory_usage > 0:
                print(f"💾 Peak Memory Usage: {memory_usage:.1f}MB")
            
            # Timing breakdown
            timing_summary = self.get_timing_summary()
            if timing_summary:
                print(f"\n📊 TIME BREAKDOWN BY COMPONENT:")
                for operation, data in sorted(timing_summary.items(), 
                                           key=lambda x: x[1]['total_time'], reverse=True):
                    total_time = data['total_time']
                    avg_time = data['avg_time']
                    count = data['count']
                    percentage = (total_time / total_build_time) * 100
                    
                    if total_time < 1.0:
                        time_str = f"{total_time*1000:.1f}ms"
                    else:
                        time_str = f"{total_time:.2f}s"
                    
                    if avg_time < 1.0:
                        avg_str = f"{avg_time*1000:.1f}ms avg"
                    else:
                        avg_str = f"{avg_time:.2f}s avg"
                    
                    print(f"  • {operation}: {time_str} ({percentage:.1f}%) - {count} ops, {avg_str}")
            
            # Performance statistics
            stats_summary = self.get_stats_summary()
            
            # Initialize totals outside the conditional block
            total_files = 0
            total_processed = 0
            total_skipped = 0
            total_errors = 0
            total_cache_hits = 0
            total_cache_misses = 0
            
            if stats_summary:
                print(f"\n📈 PERFORMANCE STATISTICS:")
                
                for category, stats in stats_summary.items():
                    if stats.total_files > 0:
                        total_files += stats.total_files
                        total_processed += stats.files_processed
                        total_skipped += stats.files_skipped
                        total_errors += stats.files_error
                        total_cache_hits += stats.cache_hits
                        total_cache_misses += stats.cache_misses
                        
                        print(f"  • {category}:")
                        print(f"    - Files: {stats.files_processed} processed, {stats.files_skipped} skipped, {stats.files_error} errors")
                        
                        if stats.processing_rate > 0:
                            print(f"    - Rate: {stats.processing_rate:.1f} files/sec")
                        
                        if stats.cache_hits + stats.cache_misses > 0:
                            print(f"    - Cache: {stats.cache_hit_rate:.1f}% hit rate ({stats.cache_hits} hits, {stats.cache_misses} misses)")
                        
                        if stats.parallel_workers > 0:
                            print(f"    - Workers: {stats.parallel_workers} parallel threads")
                
                # Overall statistics
                if total_files > 0:
                    print(f"\n  📊 OVERALL TOTALS:")
                    print(f"    - Files: {total_processed} processed, {total_skipped} skipped, {total_errors} errors")
                    
                    if total_cache_hits + total_cache_misses > 0:
                        overall_cache_rate = (total_cache_hits / (total_cache_hits + total_cache_misses)) * 100
                        print(f"    - Cache: {overall_cache_rate:.1f}% hit rate ({total_cache_hits} hits, {total_cache_misses} misses)")
            
            # Build efficiency insights
            print(f"\n🎯 BUILD INSIGHTS:")
            
            if total_build_time < 3.0:
                print("  • 🚀 Excellent build performance!")
            elif total_build_time < 10.0:
                print("  • ⚡ Good build performance")
            else:
                print("  • 🐌 Consider optimization for faster builds")
            
            # Cache effectiveness
            if total_cache_hits + total_cache_misses > 0:
                overall_cache_rate = (total_cache_hits / (total_cache_hits + total_cache_misses)) * 100
                if overall_cache_rate > 80:
                    print("  • 🎯 Excellent cache effectiveness")
                elif overall_cache_rate > 50:
                    print("  • 📈 Good cache utilization")
                else:
                    print("  • ⚠️  Low cache hit rate - consider clean build if issues")
            
            # Parallel processing efficiency
            parallel_ops = sum(1 for stats in stats_summary.values() if stats.parallel_workers > 0)
            if parallel_ops > 0:
                print("  • ⚙️  Parallel processing utilized for improved performance")
            
            print(f"{'='*60}\n")


# Global performance logger instance
logger = PerformanceLogger()


# Convenience functions for easy usage
def start_timing(operation: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """Start timing an operation"""
    return logger.start_timing(operation, metadata)


def stop_timing(timer_id: str) -> Optional[float]:
    """Stop timing an operation"""
    return logger.stop_timing(timer_id)


def time_operation(operation: str, metadata: Optional[Dict[str, Any]] = None):
    """Context manager for timing operations"""
    return logger.time_operation(operation, metadata)


def update_stats(category: str, **kwargs):
    """Update performance statistics"""
    logger.update_stats(category, **kwargs)


def log_info(component: str, message: str, emoji: str = "ℹ️", **kwargs):
    """Log an info message"""
    logger.log_info(component, message, emoji, **kwargs)


def log_debug(component: str, message: str, emoji: str = "🔍", **kwargs):
    """Log a debug message"""
    logger.log_debug(component, message, emoji, **kwargs)


def log_warn(component: str, message: str, emoji: str = "⚠️", **kwargs):
    """Log a warning message"""
    logger.log_warn(component, message, emoji, **kwargs)


def log_error(component: str, message: str, emoji: str = "❌", **kwargs):
    """Log an error message"""
    logger.log_error(component, message, emoji, **kwargs)


def log_success(component: str, message: str, emoji: str = "✅", **kwargs):
    """Log a success message"""
    logger.log_success(component, message, emoji, **kwargs)


def log_phase_start(component: str, phase: str, emoji: str = "🚀"):
    """Log the start of a build phase"""
    logger.log_phase_start(component, phase, emoji)


def log_phase_complete(component: str, phase: str, duration: float, emoji: str = "✅", **stats):
    """Log the completion of a build phase"""
    logger.log_phase_complete(component, phase, duration, emoji, **stats)


def print_build_summary():
    """Print a comprehensive build performance summary"""
    logger.print_build_summary()