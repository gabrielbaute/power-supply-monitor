import asyncio
from app.settings import settings
from app.services import NtfysService
from app.enums import NTFYPriority
from app.schemas import NTFYPayload

test_message = NTFYPayload(
    title="PRUEBA",
    event="PRUEBA",
    description="Este es un mensaje de pruebas",
    tags="test_message",
    priority=NTFYPriority.MAX
)

async def main() -> None:
    service = NtfysService(settings=settings)
    await service.emit(payload=test_message)

if __name__ == "__main__":
    print("Arrancando TEST de NTFY.")
    asyncio.run(main())
