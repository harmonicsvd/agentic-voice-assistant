"""Pydantic validation models for LLM responses."""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class OptimizedExtractionResponse(BaseModel):
    """Validated response for optimized parameter extraction."""
    detected_tool: Optional[str] = Field(
        default=None, 
        description="Name of detected skill/tool, or None if no skill detected"
    )
    extracted_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted parameters for the detected skill"
    )
    
    @validator('detected_tool')
    def validate_detected_tool(cls, v):
        """Ensure detected_tool is either None or a valid string."""
        if v is not None and not isinstance(v, str):
            logger.warning(f"detected_tool should be string or None, got {type(v)}")
            return str(v)
        return v
    
    class Config:
        extra = "forbid"  # Reject unexpected fields
        json_encoders = {
            # Custom JSON encoding if needed
        }


class ParameterExtractionResponse(BaseModel):
    """Validated response for parameter extraction (legacy)."""
    extracted_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted parameters for the current skill"
    )
    
    class Config:
        extra = "forbid"


class SkillDetectionResponse(BaseModel):
    """Validated response for skill detection (legacy)."""
    detected_tool: str = Field(
        default="none",
        description="Name of detected skill, or 'none' if no skill detected"
    )
    
    @validator('detected_tool')
    def validate_detected_tool(cls, v):
        """Ensure detected_tool is a valid string."""
        if not isinstance(v, str):
            logger.warning(f"detected_tool should be string, got {type(v)}")
            return str(v)
        return v.lower() if v else "none"
    
    class Config:
        extra = "forbid"


class ConfirmationResponse(BaseModel):
    """Validated response for confirmation detection."""
    confirmed: bool = Field(
        default=False,
        description="Whether the user confirmed the action"
    )
    
    @validator('confirmed')
    def validate_confirmed(cls, v):
        """Ensure confirmed is a boolean."""
        if not isinstance(v, bool):
            logger.warning(f"confirmed should be bool, got {type(v)}")
            # Try to parse from string
            if isinstance(v, str):
                return v.lower() in ["yes", "true", "y", "confirmed", "confirm"]
            return bool(v)
        return v
    
    class Config:
        extra = "forbid"


class LLMResponseValidator:
    """Utility class for validating LLM responses with fallback handling."""
    
    @staticmethod
    def validate_optimized_response(response_content: str) -> tuple[OptimizedExtractionResponse, bool]:
        """
        Validate optimized extraction response with fallback.
        
        Returns:
            tuple: (validated_response, success_flag)
        """
        try:
            # Clean up markdown formatting
            cleaned_content = response_content.strip()
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:]
            if cleaned_content.startswith("```"):
                cleaned_content = cleaned_content[3:]
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()
            
            # Validate with Pydantic
            validated = OptimizedExtractionResponse.model_validate_json(cleaned_content)
            logger.info(f"✅ Validation successful: detected_tool={validated.detected_tool}")
            return validated, True
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            logger.error(f"❌ Response content: {response_content[:200]}...")
            
            # Return fallback response
            fallback = OptimizedExtractionResponse(
                detected_tool="none",
                extracted_params={}
            )
            return fallback, False
    
    @staticmethod
    def validate_parameter_extraction(response_content: str) -> tuple[ParameterExtractionResponse, bool]:
        """Validate parameter extraction response with fallback."""
        try:
            cleaned_content = response_content.strip()
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:]
            if cleaned_content.startswith("```"):
                cleaned_content = cleaned_content[3:]
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()
            
            validated = ParameterExtractionResponse.model_validate_json(cleaned_content)
            logger.info(f"✅ Parameter extraction validation successful")
            return validated, True
            
        except Exception as e:
            logger.error(f"❌ Parameter extraction validation failed: {e}")
            fallback = ParameterExtractionResponse(extracted_params={})
            return fallback, False
    
    @staticmethod
    def validate_skill_detection(response_content: str) -> tuple[SkillDetectionResponse, bool]:
        """Validate skill detection response with fallback."""
        try:
            cleaned_content = response_content.strip()
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:]
            if cleaned_content.startswith("```"):
                cleaned_content = cleaned_content[3:]
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()
            
            validated = SkillDetectionResponse.model_validate_json(cleaned_content)
            logger.info(f"✅ Skill detection validation successful: {validated.detected_tool}")
            return validated, True
            
        except Exception as e:
            logger.error(f"❌ Skill detection validation failed: {e}")
            fallback = SkillDetectionResponse(detected_tool="none")
            return fallback, False
    
    @staticmethod
    def validate_confirmation(response_content: str) -> tuple[ConfirmationResponse, bool]:
        """Validate confirmation response with fallback."""
        try:
            cleaned_content = response_content.strip().lower()
            
            # Handle plain "yes"/"no" responses
            if cleaned_content in ["yes", "no"]:
                confirmed = cleaned_content == "yes"
                validated = ConfirmationResponse(confirmed=confirmed)
                logger.info(f"✅ Confirmation validation successful: {confirmed}")
                return validated, True
            
            # Handle JSON responses
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:]
            if cleaned_content.startswith("```"):
                cleaned_content = cleaned_content[3:]
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()
            
            validated = ConfirmationResponse.model_validate_json(cleaned_content)
            logger.info(f"✅ Confirmation validation successful: {validated.confirmed}")
            return validated, True
            
        except Exception as e:
            logger.error(f"❌ Confirmation validation failed: {e}")
            logger.error(f"❌ Response content: {response_content[:200]}...")
            
            # Fallback: try to parse from plain text
            cleaned_content = response_content.strip().lower()
            fallback_confirmed = cleaned_content in ["yes", "true", "y", "confirmed", "confirm"]
            fallback = ConfirmationResponse(confirmed=fallback_confirmed)
            logger.info(f"⚠️ Using fallback confirmation: {fallback_confirmed}")
            return fallback, False