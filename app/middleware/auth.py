"""
Authentication middleware for mobile apps
Handles JWT token validation and user context setup
"""
import grpc
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


class AuthInterceptor(grpc.aio.ServerInterceptor):
    """Authentication interceptor for gRPC services"""
    
    async def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], grpc.RpcMethodHandler],
        handler_call_details: grpc.HandlerCallDetails
    ) -> grpc.RpcMethodHandler:
        """Intercept gRPC calls to handle authentication"""
        
        def auth_wrapper(request, context):
            """Wrapper to add authentication logic"""
            try:
                # TODO: Implement actual JWT token validation
                # For now, this is a placeholder that allows all requests
                logger.debug(f"Processing authenticated request: {handler_call_details.method}")
                
                # Call the original handler
                handler = continuation(handler_call_details)
                if handler:
                    return handler.unary_unary(request, context)
                
            except Exception as e:
                logger.error(f"Authentication error: {str(e)}")
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Authentication failed")
        
        # Get the original handler
        handler = continuation(handler_call_details)
        
        if handler and handler.unary_unary:
            # Return a new handler with authentication wrapper
            return grpc.unary_unary_rpc_method_handler(
                auth_wrapper,
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer
            )
        
        return handler
