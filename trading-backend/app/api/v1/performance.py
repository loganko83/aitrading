"""
성능 모니터링 및 캐시 관리 API

Features:
- Cache statistics and metrics
- Performance monitoring
- Cache management (clear, warm-up)
- Response time tracking
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.core.cache import cache_manager, initialize_cache

router = APIRouter()


# Pydantic models
class CacheStats(BaseModel):
    """캐시 통계"""
    hits: int = Field(..., description="캐시 히트 횟수")
    misses: int = Field(..., description="캐시 미스 횟수")
    evictions: int = Field(..., description="캐시 축출 횟수")
    size: int = Field(..., description="현재 캐시 크기")
    hit_rate: str = Field(..., description="캐시 히트율")
    total_requests: int = Field(..., description="총 요청 수")


class AllCacheStatsResponse(BaseModel):
    """전체 캐시 통계 응답"""
    backtest: Dict[str, Any]
    market_data: Dict[str, Any]
    strategy: Dict[str, Any]
    preset: Dict[str, Any]
    pine_script: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class PerformanceStatsResponse(BaseModel):
    """성능 통계 응답"""
    operations: Dict[str, Any]
    total_metrics: int
    time_range: Dict[str, str]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class CacheClearRequest(BaseModel):
    """캐시 삭제 요청"""
    cache_type: Optional[str] = Field(
        None,
        description="삭제할 캐시 타입 (backtest, market_data, strategy, preset, pine_script). None이면 전체 삭제"
    )
    pattern: Optional[str] = Field(None, description="패턴 매칭으로 삭제 (예: 'BTCUSDT')")


class CacheClearResponse(BaseModel):
    """캐시 삭제 응답"""
    success: bool
    message: str
    cleared_caches: List[str]


class CacheWarmupResponse(BaseModel):
    """캐시 워밍업 응답"""
    success: bool
    message: str
    warmed_caches: List[str]


@router.get("/cache/stats", response_model=AllCacheStatsResponse)
async def get_cache_statistics():
    """
    전체 캐시 통계 조회

    Returns:
        - 각 캐시별 히트율, 크기, 요청 수
        - 전체 시스템 캐싱 효율성

    Use case:
        - 캐시 성능 모니터링
        - 메모리 사용량 확인
        - 최적화 지점 파악
    """
    try:
        stats = cache_manager.get_all_cache_stats()
        return AllCacheStatsResponse(**stats)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"캐시 통계 조회 실패: {str(e)}"
        )


@router.get("/cache/stats/{cache_type}")
async def get_specific_cache_stats(cache_type: str):
    """
    특정 캐시 통계 조회

    Args:
        cache_type: 캐시 타입 (backtest, market_data, strategy, preset, pine_script)

    Returns:
        - 해당 캐시의 상세 통계
    """
    try:
        cache = cache_manager.get_cache(cache_type)
        stats = cache.get_stats()

        return {
            "cache_type": cache_type,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"캐시 통계 조회 실패: {str(e)}"
        )


@router.get("/performance/stats", response_model=PerformanceStatsResponse)
async def get_performance_statistics():
    """
    성능 통계 조회

    Returns:
        - 작업별 평균 응답 시간
        - 캐시 히트율
        - 성능 트렌드

    Use case:
        - API 응답 속도 모니터링
        - 병목 지점 파악
        - 캐시 효과 측정
    """
    try:
        stats = cache_manager.get_performance_stats()

        if "message" in stats:
            # No data available
            return PerformanceStatsResponse(
                operations={},
                total_metrics=0,
                time_range={"oldest": "", "newest": ""}
            )

        return PerformanceStatsResponse(**stats)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"성능 통계 조회 실패: {str(e)}"
        )


@router.post("/cache/clear", response_model=CacheClearResponse)
async def clear_cache(request: CacheClearRequest):
    """
    캐시 삭제

    Args:
        cache_type: 삭제할 캐시 타입 (None이면 전체 삭제)
        pattern: 패턴 매칭 삭제 (예: 'BTCUSDT'로 시작하는 모든 캐시)

    Returns:
        - 삭제 성공 여부
        - 삭제된 캐시 목록

    Use case:
        - 오래된 데이터 정리
        - 메모리 확보
        - 특정 심볼 데이터 갱신
    """
    try:
        cleared = []

        if request.cache_type is None:
            # Clear all caches
            cache_manager.clear_all()
            cleared = ["backtest", "market_data", "strategy", "preset", "pine_script"]
            message = "전체 캐시가 삭제되었습니다"

        else:
            # Clear specific cache
            cache = cache_manager.get_cache(request.cache_type)

            if request.pattern:
                cache.invalidate_pattern(request.pattern)
                message = f"{request.cache_type} 캐시에서 '{request.pattern}' 패턴 삭제 완료"
            else:
                cache.clear()
                message = f"{request.cache_type} 캐시가 삭제되었습니다"

            cleared = [request.cache_type]

        return CacheClearResponse(
            success=True,
            message=message,
            cleared_caches=cleared
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"캐시 삭제 실패: {str(e)}"
        )


@router.post("/cache/cleanup")
async def cleanup_expired_cache():
    """
    만료된 캐시 정리

    Returns:
        - 정리된 캐시 수
        - 확보된 메모리 추정치

    Use case:
        - 자동 정리 작업
        - 메모리 최적화
    """
    try:
        # Get stats before cleanup
        stats_before = cache_manager.get_all_cache_stats()
        total_before = sum(
            cache_stats["size"]
            for cache_stats in stats_before.values()
        )

        # Cleanup
        cache_manager.cleanup_all()

        # Get stats after cleanup
        stats_after = cache_manager.get_all_cache_stats()
        total_after = sum(
            cache_stats["size"]
            for cache_stats in stats_after.values()
        )

        cleaned_count = total_before - total_after

        return {
            "success": True,
            "message": "만료된 캐시가 정리되었습니다",
            "cleaned_entries": cleaned_count,
            "size_before": total_before,
            "size_after": total_after,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"캐시 정리 실패: {str(e)}"
        )


@router.post("/cache/warmup", response_model=CacheWarmupResponse)
async def warmup_cache():
    """
    캐시 워밍업 (미리 로드)

    Returns:
        - 워밍업된 캐시 목록
        - 로드된 엔트리 수

    Use case:
        - 서버 시작 시 초기화
        - 성능 최적화
        - 자주 사용하는 데이터 미리 로드
    """
    try:
        initialize_cache()

        # Get updated stats
        stats = cache_manager.get_all_cache_stats()

        total_entries = sum(
            cache_stats["size"]
            for cache_stats in stats.values()
        )

        return CacheWarmupResponse(
            success=True,
            message=f"캐시 워밍업 완료: {total_entries}개 엔트리 로드됨",
            warmed_caches=["preset", "strategy"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"캐시 워밍업 실패: {str(e)}"
        )


@router.get("/performance/summary")
async def get_performance_summary():
    """
    성능 요약 대시보드

    Returns:
        - 전체 시스템 성능 개요
        - 캐시 효율성
        - 응답 시간 통계
        - 최적화 추천사항

    Use case:
        - 시스템 모니터링 대시보드
        - 성능 리포트 생성
    """
    try:
        cache_stats = cache_manager.get_all_cache_stats()
        perf_stats = cache_manager.get_performance_stats()

        # Calculate overall metrics
        total_hits = sum(cache["hits"] for cache in cache_stats.values())
        total_misses = sum(cache["misses"] for cache in cache_stats.values())
        total_requests = total_hits + total_misses
        overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0

        # Calculate average response times
        avg_response_times = {}
        if "operations" in perf_stats:
            for op, data in perf_stats["operations"].items():
                avg_response_times[op] = data["avg_duration_ms"]

        # Generate recommendations
        recommendations = []
        if overall_hit_rate < 50:
            recommendations.append("⚠️ 캐시 히트율이 낮습니다. TTL 설정을 늘리는 것을 고려하세요")
        if overall_hit_rate > 90:
            recommendations.append("✅ 캐시가 매우 효율적으로 작동하고 있습니다")

        for cache_name, cache_data in cache_stats.items():
            if cache_data["evictions"] > cache_data["size"] * 2:
                recommendations.append(
                    f"⚠️ {cache_name} 캐시의 축출이 많습니다. 캐시 크기를 늘리는 것을 고려하세요"
                )

        return {
            "summary": {
                "overall_hit_rate": f"{overall_hit_rate:.2f}%",
                "total_requests": total_requests,
                "total_cache_hits": total_hits,
                "total_cache_misses": total_misses,
                "total_cached_entries": sum(cache["size"] for cache in cache_stats.values())
            },
            "cache_performance": cache_stats,
            "response_times": avg_response_times,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"성능 요약 조회 실패: {str(e)}"
        )
