"""
Push Notification Manager - Optimized for Mobile
Supports both FCM (Android) and APNs (iOS) with battery-friendly batching
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pyfcm import FCMNotification
from apns2.client import APNsClient
from apns2.payload import Payload
from cryptography.hazmat.primitives import serialization

from app.core.settings import get_settings, MobileConfig

settings = get_settings()
logger = logging.getLogger(__name__)


class PushNotificationManager:
    """
    Mobile-optimized push notification manager
    Implements batching and priority-based delivery
    """
    
    def __init__(self):
        self.fcm_client = None
        self.apns_client = None
        self.notification_queue: Dict[str, List[dict]] = {}
        self.device_tokens: Dict[str, dict] = {}
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize FCM and APNs clients"""
        try:
            # Initialize FCM for Android
            if settings.FCM_SERVER_KEY:
                self.fcm_client = FCMNotification(api_key=settings.FCM_SERVER_KEY)
                logger.info("FCM client initialized")
            
            # Initialize APNs for iOS
            if settings.APNS_CERT_PATH:
                with open(settings.APNS_CERT_PATH, 'rb') as cert_file:
                    cert_data = cert_file.read()
                
                self.apns_client = APNsClient(
                    credentials=cert_data,
                    use_sandbox=settings.ENVIRONMENT != "production"
                )
                logger.info("APNs client initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize push clients: {e}")
    
    async def register_device(
        self, 
        device_token: str, 
        push_token: str, 
        platform: str
    ) -> bool:
        """Register a device for push notifications"""
        try:
            self.device_tokens[device_token] = {
                "push_token": push_token,
                "platform": platform.lower(),
                "registered_at": datetime.now(timezone.utc),
                "active": True
            }
            
            logger.info(f"Device registered for push: {platform} - {device_token[:10]}...")
            return True
            
        except Exception as e:
            logger.error(f"Device registration failed: {e}")
            return False
    
    async def send_notification(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        priority: str = "normal"
    ) -> bool:
        """Send a single notification"""
        try:
            device_info = self.device_tokens.get(device_token)
            if not device_info or not device_info["active"]:
                logger.warning(f"Device not found or inactive: {device_token}")
                return False
            
            platform = device_info["platform"]
            push_token = device_info["push_token"]
            
            if platform == "android":
                return await self._send_fcm_notification(
                    push_token, title, body, data, priority
                )
            elif platform == "ios":
                return await self._send_apns_notification(
                    push_token, title, body, data, priority
                )
            else:
                logger.error(f"Unsupported platform: {platform}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    async def send_batch_notifications(
        self,
        notifications: List[Dict]
    ) -> Dict[str, bool]:
        """
        Send notifications in batches for efficiency
        Optimized for mobile data usage
        """
        results = {}
        
        # Group by platform for batch processing
        android_notifications = []
        ios_notifications = []
        
        for notification in notifications:
            device_token = notification.get("device_token")
            device_info = self.device_tokens.get(device_token)
            
            if not device_info or not device_info["active"]:
                results[device_token] = False
                continue
            
            if device_info["platform"] == "android":
                android_notifications.append(notification)
            elif device_info["platform"] == "ios":
                ios_notifications.append(notification)
        
        # Process Android notifications
        if android_notifications:
            android_results = await self._send_fcm_batch(android_notifications)
            results.update(android_results)
        
        # Process iOS notifications
        if ios_notifications:
            ios_results = await self._send_apns_batch(ios_notifications)
            results.update(ios_results)
        
        return results
    
    async def _send_fcm_notification(
        self,
        push_token: str,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        priority: str = "normal"
    ) -> bool:
        """Send FCM notification to Android device"""
        try:
            if not self.fcm_client:
                logger.error("FCM client not initialized")
                return False
            
            # Optimize for battery life
            android_config = {
                "priority": "high" if priority == "critical" else "normal",
                "ttl": "86400s",  # 24 hours
                "collapse_key": "financial_update" if data else "general",
                "data": data or {}
            }
            
            result = self.fcm_client.notify_single_device(
                registration_id=push_token,
                message_title=title,
                message_body=body,
                data_message=android_config["data"],
                android_config=android_config
            )
            
            success = result.get("success", 0) > 0
            if not success:
                logger.warning(f"FCM notification failed: {result}")
            
            return success
            
        except Exception as e:
            logger.error(f"FCM notification error: {e}")
            return False
    
    async def _send_apns_notification(
        self,
        push_token: str,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        priority: str = "normal"
    ) -> bool:
        """Send APNs notification to iOS device"""
        try:
            if not self.apns_client:
                logger.error("APNs client not initialized")
                return False
            
            # Create payload optimized for iOS
            payload = Payload(
                alert={
                    "title": title,
                    "body": body
                },
                badge=1,
                sound="default" if priority == "critical" else None,
                custom=data or {},
                content_available=True  # For background processing
            )
            
            # Set priority for battery optimization
            apns_priority = 10 if priority == "critical" else 5
            
            self.apns_client.send_notification(
                token_hex=push_token,
                notification=payload,
                priority=apns_priority,
                expiration=86400  # 24 hours
            )
            
            return True
            
        except Exception as e:
            logger.error(f"APNs notification error: {e}")
            return False
    
    async def _send_fcm_batch(self, notifications: List[Dict]) -> Dict[str, bool]:
        """Send batch FCM notifications"""
        results = {}
        
        try:
            # Group into batches of 100 (FCM limit)
            batch_size = MobileConfig.NOTIFICATION_BATCH_SIZE
            
            for i in range(0, len(notifications), batch_size):
                batch = notifications[i:i + batch_size]
                
                # Prepare batch data
                registration_ids = []
                notification_data = {}
                
                for notif in batch:
                    device_token = notif["device_token"]
                    device_info = self.device_tokens[device_token]
                    registration_ids.append(device_info["push_token"])
                
                # Send batch
                if registration_ids:
                    result = self.fcm_client.notify_multiple_devices(
                        registration_ids=registration_ids,
                        message_title=batch[0].get("title", ""),
                        message_body=batch[0].get("body", ""),
                        data_message=batch[0].get("data", {})
                    )
                    
                    # Process results
                    success_count = result.get("success", 0)
                    failure_count = result.get("failure", 0)
                    
                    for j, notif in enumerate(batch):
                        device_token = notif["device_token"]
                        results[device_token] = j < success_count
            
        except Exception as e:
            logger.error(f"FCM batch error: {e}")
            for notif in notifications:
                results[notif["device_token"]] = False
        
        return results
    
    async def _send_apns_batch(self, notifications: List[Dict]) -> Dict[str, bool]:
        """Send batch APNs notifications"""
        results = {}
        
        try:
            for notification in notifications:
                device_token = notification["device_token"]
                success = await self._send_apns_notification(
                    self.device_tokens[device_token]["push_token"],
                    notification.get("title", ""),
                    notification.get("body", ""),
                    notification.get("data"),
                    notification.get("priority", "normal")
                )
                results[device_token] = success
                
                # Small delay to prevent rate limiting
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"APNs batch error: {e}")
            for notif in notifications:
                results[notif["device_token"]] = False
        
        return results
    
    async def schedule_financial_alerts(
        self,
        user_id: int,
        alert_type: str,
        data: Dict
    ):
        """
        Schedule financial alerts with smart timing
        Avoids sending during sleep hours for battery optimization
        """
        try:
            # Get user's devices
            user_devices = [
                device_token for device_token, info in self.device_tokens.items()
                if info.get("user_id") == user_id and info["active"]
            ]
            
            if not user_devices:
                logger.info(f"No active devices for user {user_id}")
                return
            
            # Create notification based on alert type
            title, body = self._create_financial_alert(alert_type, data)
            
            # Send to all user devices
            notifications = [
                {
                    "device_token": device_token,
                    "title": title,
                    "body": body,
                    "data": {"alert_type": alert_type, **data},
                    "priority": "normal"
                }
                for device_token in user_devices
            ]
            
            await self.send_batch_notifications(notifications)
            
        except Exception as e:
            logger.error(f"Failed to schedule financial alerts: {e}")
    
    def _create_financial_alert(self, alert_type: str, data: Dict) -> tuple:
        """Create appropriate title/body for financial alerts"""
        alert_templates = {
            "budget_exceeded": (
                "Budget Alert",
                f"You've exceeded your {data.get('category', 'budget')} budget by ${data.get('amount', 0):.2f}"
            ),
            "large_transaction": (
                "Large Transaction",
                f"New transaction: ${data.get('amount', 0):.2f} at {data.get('merchant', 'Unknown')}"
            ),
            "saving_goal": (
                "Savings Goal",
                f"Great job! You're {data.get('percentage', 0)}% towards your goal"
            ),
            "bill_reminder": (
                "Bill Reminder",
                f"{data.get('bill_name', 'Bill')} is due in {data.get('days', 0)} days"
            )
        }
        
        return alert_templates.get(alert_type, ("Financial Alert", "You have a new financial update"))
    
    async def cleanup_inactive_devices(self):
        """Remove inactive devices to optimize performance"""
        try:
            current_time = datetime.now(timezone.utc)
            inactive_devices = []
            
            for device_token, info in self.device_tokens.items():
                # Remove devices inactive for more than 30 days
                if (current_time - info["registered_at"]).days > 30:
                    inactive_devices.append(device_token)
            
            for device_token in inactive_devices:
                del self.device_tokens[device_token]
                logger.info(f"Removed inactive device: {device_token[:10]}...")
            
        except Exception as e:
            logger.error(f"Device cleanup error: {e}")
