"""
Main gRPC Server Entry Point
Optimized for mobile clients with binary protocol support
"""
import asyncio
import logging
import signal
import sys
from concurrent import futures
from typing import List

import grpc
from grpc_reflection.v1alpha import reflection

from app.core.settings import get_settings
from app.core.logging import setup_logging
from app.grpc_services.grpc_server import GrpcServer
from app.grpc_services.user_grpc_service import UserServicer
from app.grpc_services.transaction_grpc_service import TransactionServicer
from app.grpc_services.budget_grpc_service import BudgetServicer
from app.grpc_services.ai_advisor_grpc_service import AIAdvisorServicer
from app.middleware.mobile import MobileDeviceManager
from app.utils.push_notifications import PushNotificationManager

# Import generated gRPC modules
from app.generated import user_pb2_grpc
from app.generated import transaction_pb2_grpc
from app.generated import budget_pb2_grpc
from app.generated import ai_advisor_pb2_grpc
from app.generated import mobile_pb2_grpc

settings = get_settings()
logger = logging.getLogger(__name__)


class SpendyWiseGrpcServer:
    """Main gRPC server for SpendyWise mobile backend"""
    
    def __init__(self):
        self.server = None
        self.mobile_device_manager = MobileDeviceManager()
        self.push_notification_manager = PushNotificationManager()
        
    async def create_server(self) -> grpc.aio.Server:
        """Create and configure gRPC server with all services"""
        # Create server with optimized settings for mobile
        server = grpc.aio.server(
            futures.ThreadPoolExecutor(max_workers=settings.GRPC_MAX_WORKERS),
            options=[
                ('grpc.keepalive_time_ms', 30000),  # 30 seconds
                ('grpc.keepalive_timeout_ms', 5000),  # 5 seconds
                ('grpc.keepalive_permit_without_calls', True),
                ('grpc.http2.max_pings_without_data', 0),
                ('grpc.http2.min_time_between_pings_ms', 10000),
                ('grpc.http2.min_ping_interval_without_data_ms', 300000),
                ('grpc.max_send_message_length', 4 * 1024 * 1024),  # 4MB
                ('grpc.max_receive_message_length', 4 * 1024 * 1024),  # 4MB
                ('grpc.compression', grpc.Compression.Gzip),  # Enable compression
            ]
        )
        
        # Add all service servicers
        user_pb2_grpc.add_UserServiceServicer_to_server(UserServicer(), server)
        transaction_pb2_grpc.add_TransactionServiceServicer_to_server(TransactionServicer(), server)
        budget_pb2_grpc.add_BudgetServiceServicer_to_server(BudgetServicer(), server)
        ai_advisor_pb2_grpc.add_AIAdvisorServiceServicer_to_server(AIAdvisorServicer(), server)
        mobile_pb2_grpc.add_MobileServiceServicer_to_server(
            self.mobile_device_manager, server
        )
        
        # Add reflection service for development
        if settings.ENVIRONMENT == "development":
            SERVICE_NAMES = (
                user_pb2_grpc.UserService.full_name,
                transaction_pb2_grpc.TransactionService.full_name,
                budget_pb2_grpc.BudgetService.full_name,
                ai_advisor_pb2_grpc.AIAdvisorService.full_name,
                mobile_pb2_grpc.MobileService.full_name,
                reflection.SERVICE_NAME,
            )
            reflection.enable_server_reflection(SERVICE_NAMES, server)
        
        # Configure server address
        listen_addr = f"{settings.GRPC_HOST}:{settings.GRPC_PORT}"
        if settings.TLS_ENABLED:
            # Load TLS credentials for production
            with open(settings.TLS_CERT_PATH, 'rb') as f:
                cert_chain = f.read()
            with open(settings.TLS_KEY_PATH, 'rb') as f:
                private_key = f.read()
            
            credentials = grpc.ssl_server_credentials(
                [(private_key, cert_chain)],
                root_certificates=None,
                require_client_auth=False
            )
            server.add_secure_port(listen_addr, credentials)
        else:
            server.add_insecure_port(listen_addr)
        
        return server
    
    async def start(self):
        """Start the gRPC server"""
        setup_logging()
        logger.info("Starting SpendyWise gRPC Server...")
        
        try:
            self.server = await self.create_server()
            await self.server.start()
            
            logger.info(f"gRPC Server started on {settings.GRPC_HOST}:{settings.GRPC_PORT}")
            logger.info(f"TLS Enabled: {settings.TLS_ENABLED}")
            logger.info("Server is ready to accept connections")
            
            # Wait for termination
            await self.server.wait_for_termination()
            
        except Exception as e:
            logger.error(f"Failed to start gRPC server: {e}")
            raise
    
    async def stop(self, grace_period: int = 30):
        """Gracefully stop the gRPC server"""
        if self.server:
            logger.info("Shutting down gRPC server...")
            await self.server.stop(grace_period)
            logger.info("gRPC server stopped")


async def main():
    """Main entry point"""
    grpc_server = SpendyWiseGrpcServer()
    
    # Handle graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(grpc_server.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await grpc_server.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
