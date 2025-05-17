"""
Base Repository Pattern Implementation

This module provides a base repository class for interacting with SQLAlchemy models.
Each model type can extend this base class to reuse standard CRUD operations.
"""

from typing import Generic, TypeVar, List, Optional, Type, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from config.database import Base

# Type variable for the model
T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T]):
    """
    Base repository class for CRUD operations on SQLAlchemy models.
    """
    
    def __init__(self, session: Session, model_cls: Type[T]):
        """
        Initialize the repository with a database session and model class.
        
        Args:
            session: SQLAlchemy session for database operations
            model_cls: SQLAlchemy model class this repository handles
        """
        self.session = session
        self.model_cls = model_cls
    
    def create(self, instance: T) -> T:
        """
        Create a new instance in the database.
        
        Args:
            instance: Model instance to create
            
        Returns:
            The created instance with any database-generated values
        """
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance
    
    def get_by_id(self, id_value: Any) -> Optional[T]:
        """
        Get an instance by its primary key.
        
        Args:
            id_value: Primary key value
            
        Returns:
            The instance if found, None otherwise
        """
        return self.session.get(self.model_cls, id_value)
    
    def get_all(self) -> List[T]:
        """
        Get all instances of this model.
        
        Returns:
            List of all instances
        """
        stmt = select(self.model_cls)
        return list(self.session.scalars(stmt))
    
    def get_by_filter(self, **filters) -> List[T]:
        """
        Get instances matching the specified filters.
        
        Args:
            **filters: Field name and value pairs to filter by
            
        Returns:
            List of matching instances
        """
        stmt = select(self.model_cls)
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model_cls, field) == value)
        return list(self.session.scalars(stmt))
    
    def update(self, instance: T) -> T:
        """
        Update an existing instance in the database.
        
        Args:
            instance: Model instance to update
            
        Returns:
            The updated instance
        """
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance
    
    def update_by_id(self, id_value: Any, data: Dict[str, Any]) -> Optional[T]:
        """
        Update an instance by ID with the provided data.
        
        Args:
            id_value: Primary key value
            data: Dictionary of field name and new value pairs
            
        Returns:
            The updated instance if found, None otherwise
        """
        instance = self.get_by_id(id_value)
        if instance:
            for field, value in data.items():
                setattr(instance, field, value)
            self.session.commit()
            self.session.refresh(instance)
        return instance
    
    def delete(self, instance: T) -> bool:
        """
        Delete an instance from the database.
        
        Args:
            instance: Model instance to delete
            
        Returns:
            True if deletion was successful
        """
        self.session.delete(instance)
        self.session.commit()
        return True
    
    def delete_by_id(self, id_value: Any) -> bool:
        """
        Delete an instance by its primary key.
        
        Args:
            id_value: Primary key value
            
        Returns:
            True if deletion was successful, False if instance not found
        """
        instance = self.get_by_id(id_value)
        if instance:
            return self.delete(instance)
        return False
