"""
Health Check and Monitoring API

시스템 상태 모니터링 API - 안정성 확인, 서킷 브레이커 상태, 성능 지표
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import psutil
import logging

from app.core.stability import breaker_manager, CircuitState
from app.core.api_wrapper import degradation_manager

logger = logging.getLogger(__name__)

router = APIRouter()


class ServiceStatus(BaseModel):
    """Individual service status"""
    name: str = Field(..., description="서비스 이름")
    status: str = Field(..., description="상태 (healthy, degraded, down)")
    message: str = Field(..., description="상태 메시지")
    last_check: str = Field(..., description="마지막 확인 시간")
    details: Optional[Dict[str, Any]] = Field(None, description="상세 정보")


class CircuitBreakerStatus(BaseModel):
    """Circuit breaker status"""
    name: str = Field(..., description="서킷 브레이커 이름")
    state: str = Field(..., description="상태 (closed, open, half_open)")
    failure_count: int = Field(..., description="실패 횟수")
    success_count: int = Field(..., description="성공 횟수")
    last_failure_time: Optional[str] = Field(None, description="마지막 실패 시간")
    last_state_change: str = Field(..., description="마지막 상태 변경 시간")
    next_retry_time: Optional[str] = Field(None, description="다음 재시도 시간")
    health_percentage: float = Field(..., description="건강도 (%)")


class SystemMetrics(BaseModel):
    """System performance metrics"""
    cpu_percent: float = Field(..., description="CPU 사용률 (%)")
    memory_percent: float = Field(..., description="메모리 사용률 (%)")
    disk_percent: float = Field(..., description="디스크 사용률 (%)")
    uptime_seconds: float = Field(..., description="가동 시간 (초)")


class HealthCheckResponse(BaseModel):
    """종합 시스템 상태"""
    status: str = Field(..., description="전체 상태 (healthy, degraded, unhealthy)")
    message: str = Field(..., description="상태 메시지")
    timestamp: str = Field(..., description="확인 시간")
    services: List[ServiceStatus] = Field(..., description="서비스별 상태")
    circuit_breakers: List[CircuitBreakerStatus] = Field(..., description="서킷 브레이커 상태")
    system_metrics: SystemMetrics = Field(..., description="시스템 성능 지표")
    warnings: List[str] = Field(default_factory=list, description="경고 사항")
    recommendations: List[str] = Field(default_factory=list, description="권장 사항")


class CircuitBreakerResetRequest(BaseModel):
    """Circuit breaker reset request"""
    breaker_name: Optional[str] = Field(None, description="리셋할 서킷 브레이커 (None이면 전체)")


@router.get("/health", response_model=HealthCheckResponse)
async def get_system_health():
    """
    시스템 종합 건강 상태 확인

    Returns:
    - 전체 시스템 상태 (healthy, degraded, unhealthy)
    - 서비스별 상태 (database, cache, binance, okx)
    - 서킷 브레이커 상태
    - 시스템 리소스 사용률
    - 경고 및 권장사항
    """

    try:
        timestamp = datetime.now().isoformat()

        # 1. Check circuit breakers
        breaker_statuses = []
        all_breakers_status = breaker_manager.get_all_status()

        for breaker_name, breaker_info in all_breakers_status.items():
            # Calculate health percentage
            if breaker_info["state"] == "closed":
                health = 100.0
            elif breaker_info["state"] == "half_open":
                health = 50.0
            else:  # open
                health = 0.0

            breaker_statuses.append(CircuitBreakerStatus(
                name=breaker_name,
                state=breaker_info["state"],
                failure_count=breaker_info["failure_count"],
                success_count=breaker_info["success_count"],
                last_failure_time=breaker_info.get("last_failure_time"),
                last_state_change=breaker_info["last_state_change"],
                next_retry_time=breaker_info.get("next_retry_time"),
                health_percentage=health
            ))

        # 2. Check service degradation
        service_statuses = []
        degraded_services = degradation_manager.get_all_status()

        # Always include core services
        core_services = ["database", "cache", "binance_api", "okx_api"]

        for service in core_services:
            if service in degraded_services and degraded_services[service]["degraded"]:
                status = ServiceStatus(
                    name=service,
                    status="degraded",
                    message=degraded_services[service]["reason"],
                    last_check=timestamp,
                    details={"degraded": True}
                )
            else:
                status = ServiceStatus(
                    name=service,
                    status="healthy",
                    message="Service is operating normally",
                    last_check=timestamp,
                    details={"degraded": False}
                )

            service_statuses.append(status)

        # 3. Get system metrics
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            uptime = datetime.now().timestamp() - psutil.boot_time()

            system_metrics = SystemMetrics(
                cpu_percent=round(cpu_percent, 2),
                memory_percent=round(memory_info.percent, 2),
                disk_percent=round(disk_info.percent, 2),
                uptime_seconds=round(uptime, 2)
            )
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            system_metrics = SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                uptime_seconds=0.0
            )

        # 4. Determine overall status
        warnings = []
        recommendations = []

        # Check circuit breakers
        open_breakers = [b for b in breaker_statuses if b.state == "open"]
        half_open_breakers = [b for b in breaker_statuses if b.state == "half_open"]

        if open_breakers:
            warnings.append(
                f"⚠️ {len(open_breakers)}개의 서킷 브레이커가 OPEN 상태입니다: "
                f"{', '.join(b.name for b in open_breakers)}"
            )
            recommendations.append(
                "서킷 브레이커가 OPEN 상태인 서비스는 일시적으로 사용할 수 없습니다. "
                "자동 복구를 기다리거나 수동으로 리셋하세요."
            )

        if half_open_breakers:
            warnings.append(
                f"🔄 {len(half_open_breakers)}개의 서킷 브레이커가 복구 테스트 중입니다: "
                f"{', '.join(b.name for b in half_open_breakers)}"
            )

        # Check degraded services
        degraded = [s for s in service_statuses if s.status == "degraded"]
        if degraded:
            warnings.append(
                f"⚠️ {len(degraded)}개의 서비스가 성능 저하 상태입니다: "
                f"{', '.join(s.name for s in degraded)}"
            )

        # Check system resources
        if system_metrics.cpu_percent > 80:
            warnings.append(f"⚠️ CPU 사용률이 높습니다: {system_metrics.cpu_percent}%")
            recommendations.append("CPU 사용률이 높습니다. 백그라운드 작업을 확인하세요.")

        if system_metrics.memory_percent > 85:
            warnings.append(f"⚠️ 메모리 사용률이 높습니다: {system_metrics.memory_percent}%")
            recommendations.append("메모리 부족 위험이 있습니다. 불필요한 프로세스를 종료하세요.")

        if system_metrics.disk_percent > 90:
            warnings.append(f"⚠️ 디스크 사용률이 높습니다: {system_metrics.disk_percent}%")
            recommendations.append("디스크 공간이 부족합니다. 불필요한 파일을 삭제하세요.")

        # Determine overall status
        if open_breakers or degraded or system_metrics.cpu_percent > 90:
            overall_status = "unhealthy"
            message = "시스템이 비정상 상태입니다. 즉시 조치가 필요합니다."
        elif half_open_breakers or system_metrics.cpu_percent > 70 or system_metrics.memory_percent > 70:
            overall_status = "degraded"
            message = "시스템이 성능 저하 상태입니다. 모니터링이 필요합니다."
        else:
            overall_status = "healthy"
            message = "모든 시스템이 정상 작동 중입니다."
            recommendations.append("✅ 시스템이 안정적으로 작동하고 있습니다.")

        return HealthCheckResponse(
            status=overall_status,
            message=message,
            timestamp=timestamp,
            services=service_statuses,
            circuit_breakers=breaker_statuses,
            system_metrics=system_metrics,
            warnings=warnings,
            recommendations=recommendations
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"시스템 상태 확인 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/health/circuit-breakers", response_model=List[CircuitBreakerStatus])
async def get_circuit_breaker_status():
    """
    서킷 브레이커 상태만 조회

    Returns:
    - 모든 서킷 브레이커의 상세 상태
    """

    try:
        breaker_statuses = []
        all_breakers_status = breaker_manager.get_all_status()

        for breaker_name, breaker_info in all_breakers_status.items():
            if breaker_info["state"] == "closed":
                health = 100.0
            elif breaker_info["state"] == "half_open":
                health = 50.0
            else:
                health = 0.0

            breaker_statuses.append(CircuitBreakerStatus(
                name=breaker_name,
                state=breaker_info["state"],
                failure_count=breaker_info["failure_count"],
                success_count=breaker_info["success_count"],
                last_failure_time=breaker_info.get("last_failure_time"),
                last_state_change=breaker_info["last_state_change"],
                next_retry_time=breaker_info.get("next_retry_time"),
                health_percentage=health
            ))

        return breaker_statuses

    except Exception as e:
        logger.error(f"Failed to get circuit breaker status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"서킷 브레이커 상태 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/health/circuit-breakers/reset")
async def reset_circuit_breakers(request: CircuitBreakerResetRequest):
    """
    서킷 브레이커 수동 리셋

    Args:
    - breaker_name: 리셋할 서킷 브레이커 이름 (None이면 전체 리셋)

    Returns:
    - 리셋 결과
    """

    try:
        if request.breaker_name:
            # Reset specific breaker
            breaker_manager.reset(request.breaker_name)
            message = f"서킷 브레이커 '{request.breaker_name}'가 CLOSED 상태로 리셋되었습니다."
        else:
            # Reset all breakers
            breaker_manager.reset_all()
            message = "모든 서킷 브레이커가 CLOSED 상태로 리셋되었습니다."

        logger.info(message)

        return {
            "success": True,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to reset circuit breakers: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"서킷 브레이커 리셋 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/health/metrics", response_model=SystemMetrics)
async def get_system_metrics():
    """
    시스템 리소스 사용률만 조회

    Returns:
    - CPU, 메모리, 디스크 사용률
    - 시스템 가동 시간
    """

    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        uptime = datetime.now().timestamp() - psutil.boot_time()

        return SystemMetrics(
            cpu_percent=round(cpu_percent, 2),
            memory_percent=round(memory_info.percent, 2),
            disk_percent=round(disk_info.percent, 2),
            uptime_seconds=round(uptime, 2)
        )

    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"시스템 지표 조회 중 오류가 발생했습니다: {str(e)}"
        )
