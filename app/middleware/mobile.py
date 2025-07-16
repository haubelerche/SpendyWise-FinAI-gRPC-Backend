"""
Mobile Device Manager - gRPC Service Implementation
Optimized for battery life and data usage
"""
import asyncio
import gzip
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, AsyncGenerator

import grpc
from google.protobuf import empty_pb2, timestamp_pb2

# Import generated gRPC modules
from app.generated import mobile_pb2
from app.generated import mobile_pb2_grpc

from app.core.settings import get_settings, MobileConfig
from app.db.session import get_async_db
from app.models.user import User
from app.utils.push_notifications import PushNotificationManager
from app.core.auth import verify_token

settings = get_settings()
logger = logging.getLogger(__name__)


class MobileDeviceManager:
    """
    gRPC service for mobile device management
    Implements binary protocol with compression and streaming
    """
    
    def __init__(self):
        self.push_manager = PushNotificationManager()
        self.active_streams: Dict[str, List[grpc.aio.StreamStreamCall]] = {}
        self.device_registry: Dict[str, dict] = {}
        
    async def RegisterDevice(self, request, context):
        """Register a new mobile device"""
        try:
            # Verify user token
            user = await verify_token(request.user_token)
            if not user:
                context.set_code(grpc.StatusCode.UNAUTHENTICATED)
                context.set_details("Invalid user token")
                return
            
            # Generate device token
            device_token = f"device_{user.id}_{request.device_info.device_id}_{int(time.time())}"
            
            # Store device info
            device_data = {
                "user_id": user.id,
                "device_id": request.device_info.device_id,
                "platform": request.device_info.platform,
                "app_version": request.device_info.app_version,
                "os_version": request.device_info.os_version,
                "device_model": request.device_info.device_model,
                "timezone": request.device_info.timezone,
                "locale": request.device_info.locale,
                "push_enabled": request.device_info.push_enabled,
                "last_active": datetime.now(timezone.utc),
                "registered_at": datetime.now(timezone.utc)
            }
            
            self.device_registry[device_token] = device_data
            
            # Save to database
            async with get_async_db() as db:
                # Implementation would save to database
                pass
            
            # Return response with optimized sync interval
            sync_interval = self._calculate_sync_interval(request.device_info.platform)
            
            return mobile_pb2.DeviceRegistrationResponse(
                success=True,
                device_token=device_token,
                message="Device registered successfully",
                sync_interval_seconds=sync_interval
            )
            
        except Exception as e:
            logger.error(f"Device registration error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return mobile_pb2.DeviceRegistrationResponse(success=False, message=str(e))
    
    async def RegisterForPushNotifications(self, request, context):
        """Register device for push notifications"""
        try:
            device_data = self.device_registry.get(request.device_token)
            if not device_data:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Device not found")
                return
            
            # Register with push notification service
            success = await self.push_manager.register_device(
                device_token=request.device_token,
                push_token=request.push_token,
                platform=request.platform
            )
            
            if success:
                device_data["push_token"] = request.push_token
                device_data["push_platform"] = request.platform
                device_data["push_registered_at"] = datetime.now(timezone.utc)
            
            return mobile_pb2.PushTokenResponse(
                success=success,
                message="Push notifications registered" if success else "Registration failed"
            )
            
        except Exception as e:
            logger.error(f"Push registration error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return mobile_pb2.PushTokenResponse(success=False, message=str(e))
    
    async def StreamFinancialUpdates(self, request, context) -> AsyncGenerator:
        """
        Stream real-time financial updates using HTTP/2
        Optimized for mobile battery life with connection reuse
        """
        try:
            device_data = self.device_registry.get(request.device_token)
            if not device_data:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Device not found")
                return
            
            # Add to active streams
            user_id = device_data["user_id"]
            if user_id not in self.active_streams:
                self.active_streams[user_id] = []
            self.active_streams[user_id].append(context)
            
            try:
                # Send initial data
                sync_data = await self._get_initial_sync_data(user_id, request.categories)
                for update in sync_data:
                    yield update
                
                # Stream updates with keep-alive
                last_ping = time.time()
                while True:
                    # Check for new updates
                    updates = await self._check_for_updates(user_id, request.categories)
                    for update in updates:
                        yield update
                    
                    # Send keep-alive ping
                    current_time = time.time()
                    if current_time - last_ping > MobileConfig.KEEP_ALIVE_INTERVAL:
                        ping_update = mobile_pb2.FinancialUpdate(
                            update_id=f"ping_{int(current_time)}",
                            category="system",
                            action="ping",
                            data=b"",
                            timestamp=timestamp_pb2.Timestamp()
                        )
                        ping_update.timestamp.GetCurrentTime()
                        yield ping_update
                        last_ping = current_time
                    
                    # Battery-friendly sleep
                    await asyncio.sleep(5)
                    
            finally:
                # Clean up stream
                if user_id in self.active_streams:
                    try:
                        self.active_streams[user_id].remove(context)
                        if not self.active_streams[user_id]:
                            del self.active_streams[user_id]
                    except ValueError:
                        pass
                        
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
    
    async def GetSyncData(self, request, context):
        """
        Get compressed sync data for battery optimization
        Uses binary protocol with gzip compression
        """
        try:
            device_data = self.device_registry.get(request.device_token)
            if not device_data:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Device not found")
                return
            
            user_id = device_data["user_id"]
            
            # Get data since last sync
            sync_data = await self._get_sync_data(
                user_id, 
                request.last_sync, 
                request.data_types
            )
            
            # Compress data if requested
            if request.compressed:
                json_data = json.dumps(sync_data).encode('utf-8')
                compressed_data = gzip.compress(json_data)
            else:
                compressed_data = json.dumps(sync_data).encode('utf-8')
            
            # Update last sync time
            device_data["last_sync"] = datetime.now(timezone.utc)
            
            return mobile_pb2.SyncResponse(
                compressed_data=compressed_data,
                sync_timestamp=timestamp_pb2.Timestamp(),
                total_records=len(sync_data.get('records', [])),
                more_data_available=len(sync_data.get('records', [])) >= 1000,
                next_page_token=sync_data.get('next_page_token', '')
            )
            
        except Exception as e:
            logger.error(f"Sync error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
    
    async def UploadBatch(self, request, context):
        """
        Process batch operations for data efficiency
        """
        try:
            device_data = self.device_registry.get(request.device_token)
            if not device_data:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Device not found")
                return
            
            results = []
            processed_count = 0
            error_count = 0
            
            for operation in request.operations:
                try:
                    result = await self._process_batch_operation(
                        device_data["user_id"], 
                        operation
                    )
                    results.append(mobile_pb2.BatchResult(
                        operation_id=operation.operation_id,
                        success=True,
                        result_data=result
                    ))
                    processed_count += 1
                except Exception as op_error:
                    results.append(mobile_pb2.BatchResult(
                        operation_id=operation.operation_id,
                        success=False,
                        error_message=str(op_error)
                    ))
                    error_count += 1
            
            return mobile_pb2.BatchResponse(
                results=results,
                processed_count=processed_count,
                error_count=error_count
            )
            
        except Exception as e:
            logger.error(f"Batch upload error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
    
    async def Ping(self, request, context):
        """Health check and latency measurement"""
        response_time = timestamp_pb2.Timestamp()
        response_time.GetCurrentTime()
        
        return mobile_pb2.PingResponse(
            server_time=response_time,
            round_trip_ms=0  # Client will calculate
        )
    
    # Helper methods
    def _calculate_sync_interval(self, platform: str) -> int:
        """Calculate optimal sync interval based on platform"""
        base_interval = 300  # 5 minutes
        if platform.lower() == "ios":
            return base_interval + 60  # iOS background processing
        return base_interval
    
    async def _get_initial_sync_data(self, user_id: int, categories: List[str]) -> List:
        """Get initial data for streaming"""
        # Implementation would fetch from database
        return []
    
    async def _check_for_updates(self, user_id: int, categories: List[str]) -> List:
        """Check for new updates to stream"""
        # Implementation would check for changes
        return []
    
    async def _get_sync_data(self, user_id: int, last_sync, data_types: List[str]) -> dict:
        """Get sync data since last sync"""
        # Implementation would fetch incremental data
        return {"records": [], "next_page_token": ""}
    
    async def _process_batch_operation(self, user_id: int, operation) -> bytes:
        """Process a single batch operation"""
        # Implementation would handle the operation
        return b""
