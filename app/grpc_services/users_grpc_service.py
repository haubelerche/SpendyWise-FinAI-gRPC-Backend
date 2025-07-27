# User gRPC service implementation
import grpc
from typing import Iterator
import logging

from app.generated import users_pb2, users_pb2_grpc
from app.core.auth import require_auth, optional_auth, require_role, get_current_user_id
from app.core.exceptions import ValidationError, NotFoundError

logger = logging.getLogger(__name__)


class UserService(user_pb2_grpc.UserServiceServicer):
    """User management gRPC service with Supabase authentication"""
    
    @require_auth
    def GetProfile(self, request: user_pb2.GetProfileRequest, context: grpc.ServicerContext) -> user_pb2.ProfileResponse:
        """
        Get user profile - requires authentication
        User can only access their own profile unless they're admin
        """
        try:
            # Get authenticated user ID from context (set by @require_auth decorator)
            current_user_id = get_current_user_id(context)
            
            # Check if user is trying to access their own profile or if they're admin
            requested_user_id = request.user_id or current_user_id
            
            if requested_user_id != current_user_id and not hasattr(context, 'user_role') or context.user_role != 'admin':
                context.abort(grpc.StatusCode.PERMISSION_DENIED, "Cannot access other user's profile")
                return
            
            # TODO: Implement actual database query to get user profile
            # This is just a placeholder response
            return user_pb2.ProfileResponse(
                user_id=requested_user_id,
                email=context.user_email,
                name="User Name",
                created_at="2024-01-01T00:00:00Z"
            )
            
        except ValidationError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
        except NotFoundError as e:
            context.abort(grpc.StatusCode.NOT_FOUND, str(e))
        except Exception as e:
            logger.error(f"Error in GetProfile: {str(e)}")
            context.abort(grpc.StatusCode.INTERNAL, "Internal server error")
    
    @require_auth
    def UpdateProfile(self, request: user_pb2.UpdateProfileRequest, context: grpc.ServicerContext) -> user_pb2.ProfileResponse:
        """
        Update user profile - requires authentication
        Users can only update their own profile
        """
        try:
            current_user_id = get_current_user_id(context)
            
            # Validate input
            if not request.name and not request.phone:
                context.abort(grpc.StatusCode.INVALID_ARGUMENT, "At least one field must be provided")
                return
            
            # TODO: Implement actual database update
            logger.info(f"Updating profile for user {current_user_id}")
            
            return user_pb2.ProfileResponse(
                user_id=current_user_id,
                email=context.user_email,
                name=request.name or "Updated Name",
                phone=request.phone,
                updated_at="2024-01-01T00:00:00Z"
            )
            
        except Exception as e:
            logger.error(f"Error in UpdateProfile: {str(e)}")
            context.abort(grpc.StatusCode.INTERNAL, "Internal server error")
    
    @require_role('admin')
    def DeleteUser(self, request: user_pb2.DeleteUserRequest, context: grpc.ServicerContext) -> user_pb2.DeleteResponse:
        """
        Delete user - requires admin role
        """
        try:
            if not request.user_id:
                context.abort(grpc.StatusCode.INVALID_ARGUMENT, "User ID is required")
                return
            
            # TODO: Implement actual user deletion
            logger.info(f"Admin {context.user_id} deleting user {request.user_id}")
            
            return user_pb2.DeleteResponse(
                success=True,
                message=f"User {request.user_id} deleted successfully"
            )
            
        except Exception as e:
            logger.error(f"Error in DeleteUser: {str(e)}")
            context.abort(grpc.StatusCode.INTERNAL, "Internal server error")
    
    @optional_auth
    def GetPublicStats(self, request: user_pb2.PublicStatsRequest, context: grpc.ServicerContext) -> user_pb2.StatsResponse:
        """
        Get public statistics - authentication optional
        If authenticated, may return personalized data
        """
        try:
            # Check if user is authenticated
            if hasattr(context, 'user') and context.user:
                # Return personalized stats
                logger.info(f"Returning personalized stats for user {context.user_id}")
                return user_pb2.StatsResponse(
                    total_users=1000,
                    active_users=750,
                    personalized_message=f"Welcome back, {context.user_email}!"
                )
            else:
                # Return public stats only
                logger.info("Returning public stats for anonymous user")
                return user_pb2.StatsResponse(
                    total_users=1000,
                    active_users=750,
                    personalized_message="Sign up to see personalized insights!"
                )
                
        except Exception as e:
            logger.error(f"Error in GetPublicStats: {str(e)}")
            context.abort(grpc.StatusCode.INTERNAL, "Internal server error")
