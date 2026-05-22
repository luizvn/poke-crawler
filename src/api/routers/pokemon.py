from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.schemas import CrawlRequest, CrawlResponse
from src.services.crawler_service import CrawlerService
from src.db.database import get_db

router = APIRouter(prefix="/api/v1/pokemon", tags=["Pokemon Crawler"])


@router.post("/crawl", response_model=CrawlResponse, status_code=status.HTTP_207_MULTI_STATUS)
async def crawl_pokemons(request: CrawlRequest, db: AsyncSession = Depends(get_db)):
    """
    Executa o processo de extração e sincronização de dados de Pokémon.

    Este endpoint processa uma lista de nomes em duas etapas:
    1. **Verificação Local**: Consulta se o Pokémon já existe no banco de dados.
    2. **Extração Externa**: Caso não exista (ou `request.force_update=True`), utiliza um crawler para 
       obter dados atualizados da Bulbapedia.

    **Comportamento do Status 207 (Multi-Status):**
    Como esta é uma operação em lote, o status 207 indica que a requisição foi processada, 
    mas o resultado individual de cada Pokémon pode variar entre sucesso e falha (ex: nome inválido).

    - **successful**: Lista de nomes que foram processados e salvos/atualizados com sucesso.
    - **failed**: Lista de nomes que falharam durante o fetch ou parse, acompanhados do motivo.

    :param request: Objeto contendo a lista de nomes (`names`) e a opção de forçar atualização (`force_update`).
    """
    if not request.names:
        raise HTTPException(status_code=400, detail="A lista de nomes não pode estar vazia.")

    crawler_service = CrawlerService(db)

    successful, failed = await crawler_service.process_pokemon_list(request.names, request.force_update)

    return CrawlResponse(
        successful=successful,
        failed=failed
    )