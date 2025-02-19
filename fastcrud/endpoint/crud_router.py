from typing import Type, TypeVar, Optional, Callable, List
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel
from .endpoint_creator import EndpointCreator
from ..crud.fast_crud import FastCRUD

CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
DeleteSchemaType = TypeVar("DeleteSchemaType", bound=BaseModel)


def crud_router(
    session: AsyncSession,
    model: DeclarativeBase,
    crud: FastCRUD,
    create_schema: Type[CreateSchemaType],
    update_schema: Type[UpdateSchemaType],
    delete_schema: Optional[Type[DeleteSchemaType]] = None,
    path: str = "",
    tags: Optional[List[str]] = None,
    include_in_schema: bool = True,
    create_deps: List[Callable] = [],
    read_deps: List[Callable] = [],
    read_multi_deps: List[Callable] = [],
    update_deps: List[Callable] = [],
    delete_deps: List[Callable] = [],
    db_delete_deps: List[Callable] = [],
    included_methods: Optional[list[str]] = None,
    deleted_methods: Optional[list[str]] = None,
    endpoint_creator: Optional[Type[EndpointCreator]] = None,
    is_deleted_column: str = "is_deleted",
    deleted_at_column: str = "deleted_at",
) -> APIRouter:
    """
    Creates and configures a FastAPI router with CRUD endpoints for a given model.

    This utility function streamlines the process of setting up a router for CRUD operations,
    using a custom `EndpointCreator` if provided, and managing dependency injections as well
    as selective method inclusions or exclusions.

    Args:
        session: The SQLAlchemy async session.
        model: The SQLAlchemy model.
        crud: The FastCRUD instance.
        create_schema: Pydantic schema for creating an item.
        update_schema: Pydantic schema for updating an item.
        delete_schema: Optional Pydantic schema for deleting an item.
        path: Base path for the CRUD endpoints.
        tags: Optional list of tags for grouping endpoints in the documentation.
        include_in_schema: Whether to include the created endpoints in the OpenAPI schema.
        create_deps: Optional list of dependency injection functions for the create endpoint.
        read_deps: Optional list of dependency injection functions for the read endpoint.
        read_multi_deps: Optional list of dependency injection functions for the read multiple items endpoint.
        update_deps: Optional list of dependency injection functions for the update endpoint.
        delete_deps: Optional list of dependency injection functions for the delete endpoint.
        db_delete_deps: Optional list of dependency injection functions for the hard delete endpoint.
        included_methods: Optional list of CRUD methods to include. If None, all methods are included.
        deleted_methods: Optional list of CRUD methods to exclude.
        endpoint_creator: Optional custom class derived from EndpointCreator for advanced customization.
        is_deleted_column: Optional column name to use for indicating a soft delete. Defaults to "is_deleted".
        deleted_at_column: Optional column name to use for storing the timestamp of a soft delete. Defaults to "deleted_at".

    Returns:
        Configured APIRouter instance with the CRUD endpoints.

    Raises:
        ValueError: If both 'included_methods' and 'deleted_methods' are provided.

    Examples:
        Basic Setup:
        ```python
        router = crud_router(
            session=async_session,
            model=MyModel,
            crud=CRUDMyModel(MyModel),
            create_schema=CreateMyModelSchema,
            update_schema=UpdateMyModelSchema,
            path="/mymodel",
            tags=["MyModel"]
        )
        ```

        With Custom Dependencies:
        ```python
        def get_current_user(token: str = Depends(oauth2_scheme)):
            # Implement user retrieval logic
            return ...

        router = crud_router(
            session=async_session,
            model=UserModel,
            crud=CRUDUserModel(UserModel),
            create_schema=CreateUserSchema,
            update_schema=UpdateUserSchema,
            read_deps=[get_current_user],
            update_deps=[get_current_user],
            path="/users",
            tags=["Users"]
        )
        ```

        Adding Delete Endpoints:
        ```python
        router = crud_router(
            session=async_session,
            model=ProductModel,
            crud=CRUDProductModel(ProductModel),
            create_schema=CreateProductSchema,
            update_schema=UpdateProductSchema,
            delete_schema=DeleteProductSchema,
            path="/products",
            tags=["Products"]
        )
        ```

        Customizing Path and Tags:
        ```python
        router = crud_router(
            session=async_session,
            model=OrderModel,
            crud=CRUDOrderModel(OrderModel),
            create_schema=CreateOrderSchema,
            update_schema=UpdateOrderSchema,
            path="/orders",
            tags=["Orders", "Sales"]
        )
        ```

        Integrating Multiple Models:
        ```python
        product_router = crud_router(
            session=async_session,
            model=ProductModel,
            crud=CRUDProductModel(ProductModel),
            create_schema=CreateProductSchema,
            update_schema=UpdateProductSchema,
            path="/products",
            tags=["Inventory"]
        )

        customer_router = crud_router(
            session=async_session,
            model=CustomerModel,
            crud=CRUDCustomerModel(CustomerModel),
            create_schema=CreateCustomerSchema,
            update_schema=UpdateCustomerSchema,
            path="/customers",
            tags=["CRM"]
        )
        ```

        With Selective CRUD Methods:
        ```python
        # Only include 'create' and 'read' methods
        router = crud_router(
            session=async_session,
            model=MyModel,
            crud=CRUDMyModel(MyModel),
            create_schema=CreateMyModel,
            update_schema=UpdateMyModel,
            included_methods=["create", "read"],
            path="/mymodel",
            tags=["MyModel"]
        )
        ```

        Using a Custom EndpointCreator:
        ```python
        class CustomEndpointCreator(EndpointCreator):
            def _custom_route(self):
                async def custom_endpoint():
                    # Custom endpoint logic
                    return {"message": "Custom route"}

                return custom_endpoint

                async def add_routes_to_router(self, ...):
                    # First, add standard CRUD routes
                    super().add_routes_to_router(...)

                    # Now, add custom routes
                    self.router.add_api_route(
                        path="/custom",
                        endpoint=self._custom_route(),
                        methods=["GET"],
                        tags=self.tags,
                        # Other parameters as needed
                    )

        router = crud_router(
            session=async_session,
            model=MyModel,
            crud=CRUDMyModel(MyModel),
            create_schema=CreateMyModel,
            update_schema=UpdateMyModel,
            endpoint_creator=CustomEndpointCreator,
            path="/mymodel",
            tags=["MyModel"]
        )

        app.include_router(my_router)
        ```
    """
    endpoint_creator_class = endpoint_creator or EndpointCreator
    endpoint_creator_instance = endpoint_creator_class(
        session=session,
        model=model,
        crud=crud,
        create_schema=create_schema,
        update_schema=update_schema,
        include_in_schema=include_in_schema,
        delete_schema=delete_schema,
        path=path,
        tags=tags,
        is_deleted_column=is_deleted_column,
        deleted_at_column=deleted_at_column,
    )

    endpoint_creator_instance.add_routes_to_router(
        create_deps=create_deps,
        read_deps=read_deps,
        read_multi_deps=read_multi_deps,
        update_deps=update_deps,
        delete_deps=delete_deps,
        db_delete_deps=db_delete_deps,
        included_methods=included_methods,
        deleted_methods=deleted_methods,
    )

    return endpoint_creator_instance.router
