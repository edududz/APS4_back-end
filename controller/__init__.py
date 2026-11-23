from controller.evento_controller import router as evento_router
from controller.participante_controller import router as participante_router
from controller.inscricao_controller import router as inscricao_router
from controller.relatorio_controller import router as relatorio_router

__all__ = [
    "evento_router",
    "participante_router",
    "inscricao_router",
    "relatorio_router"
]

