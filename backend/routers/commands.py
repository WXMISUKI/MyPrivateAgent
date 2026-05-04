from fastapi import APIRouter

try:
    from services.command_registry_service import get_command_registry_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.command_registry_service import get_command_registry_service


router = APIRouter(prefix="/api/commands", tags=["commands"])


@router.get("")
def list_commands():
    return get_command_registry_service().list_commands()
