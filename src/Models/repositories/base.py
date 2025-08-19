"""
Base Repository class providing common CRUD operations.

This module contains the abstract base repository class that all
specific repository classes should inherit from.
"""

from abc import ABC, abstractmethod
from typing import Type, TypeVar, Generic, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import update, delete, and_, or_
from uuid import UUID

from ..DBSchemes.Schemes.base import BaseModel

# Type variable for the model
ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType], ABC):
    """
    Abstract base repository class providing common CRUD operations.
    
    This class should be inherited by all specific repository classes.
    It provides async database operations using SQLAlchemy.
    """
    
    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        """
        Initialize the repository with a database session and model.
        
        Args:
            session: Async SQLAlchemy session
            model: SQLAlchemy model class
            
        """
        
        self.session = session
        self.model = model
    
    async def create(self, **kwargs) -> ModelType:
        """
        Create a new record in the database.
        
        Args:
            **kwargs: Field values for the new record
            
        Returns:
            The created model instance
            
        Raises:
            ValueError: If data violates constraints or is invalid
        """
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            await self.session.flush()  # Flush to get DB-generated values without committing
            await self.session.refresh(instance)
            return instance
        except Exception as e:
            # Let get_db_session handle rollback - don't rollback here
            raise ValueError(f"Failed to create {self.model.__name__}: {str(e)}")
    
    
    async def get_by_id(self, record_id: UUID) -> Optional[ModelType]:
        """
        Get a record by its ID.
        
        Args:
            record_id: UUID of the record
            
        Returns:
            The model instance or None if not found
        """
        result = await self.session.execute(
            select(self.model).where(self._get_id_field() == record_id)
        )
        return result.scalar_one_or_none()
    
    
    async def get_all(
        self, 
        offset: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """
        Get all records with optional filtering and pagination.
        
        Args:
            offset: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional filters to apply
            
        Returns:
            List of model instances
        """
        query = select(self.model)
        
        if filters:
            conditions = []
            for field, value in filters.items():
                if hasattr(self.model, field):
                    conditions.append(getattr(self.model, field) == value)
            if conditions:
                query = query.where(and_(*conditions))
        
        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update(self, record_id: UUID, **kwargs) -> Optional[ModelType]:
        """
        Update a record by its ID.
        
        Args:
            record_id: UUID of the record to update
            **kwargs: Field values to update
            
        Returns:
            The updated model instance or None if not found
        """
        # Remove None values from kwargs
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        
        if not update_data:
            return await self.get_by_id(record_id)
        
        result = await self.session.execute(
            update(self.model)
            .where(self._get_id_field() == record_id)
            .values(**update_data)
            .returning(self.model)
        )
        
        updated_instance = result.scalar_one_or_none()
        if updated_instance:
            await self.session.flush()  # Flush to persist changes without committing
            await self.session.refresh(updated_instance)
        
        return updated_instance
    
    async def delete(self, record_id: UUID) -> bool:
        """
        Delete a record by its ID.
        
        Args:
            record_id: UUID of the record to delete
            
        Returns:
            True if deleted, False if not found
        """
        result = await self.session.execute(
            delete(self.model).where(self._get_id_field() == record_id)
        )
        await self.session.flush()  # Flush to persist deletion without committing
        return result.rowcount > 0
    
    async def exists(self, record_id: UUID) -> bool:
        """
        Check if a record exists by its ID.
        
        Args:
            record_id: UUID of the record
            
        Returns:
            True if exists, False otherwise
        """
        result = await self.session.execute(
            select(self.model).where(self._get_id_field() == record_id)
        )
        return result.scalar_one_or_none() is not None
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filtering.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Number of matching records
        """
        from sqlalchemy import func
        
        query = select(func.count(self._get_id_field()))
        
        if filters:
            conditions = []
            for field, value in filters.items():
                if hasattr(self.model, field):
                    conditions.append(getattr(self.model, field) == value)
            if conditions:
                query = query.where(and_(*conditions))
        
        result = await self.session.execute(query)
        return result.scalar()
    
    def _get_id_field(self):
        """
        Get the primary key field of the model.
        This method should be overridden in child classes if needed.
        """
        # Get the first primary key column
        primary_keys = [col for col in self.model.__table__.columns if col.primary_key]
        if primary_keys:
            return primary_keys[0]
        raise ValueError(f"No primary key found for model {self.model.__name__}")
    
    @abstractmethod
    def get_model_specific_methods(self):
        """
        Abstract method to be implemented by child classes
        for model-specific operations.
        """
        pass
