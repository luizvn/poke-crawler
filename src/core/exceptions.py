class PokeCrawlerException(Exception):
    """Exceção base para o projeto PokéCrawler."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class CrawlerFetchError(PokeCrawlerException):
    """Erro ao tentar buscar dados na web."""
    pass


class CloudflareBlockError(CrawlerFetchError):
    """Erro específico para quando o Cloudflare impede o acesso."""
    pass


class ImageDownloadError(CrawlerFetchError):
    """Erro ao tentar baixar a imagem do Pokémon."""
    pass


class CrawlerParseError(PokeCrawlerException):
    """Erro base para falhas de extração no HTML."""
    pass


class FieldExtractionError(CrawlerParseError):
    """Erro lançado quando um campo obrigatório não pôde ser extraído."""
    def __init__(self, field: str, message: str):
        super().__init__(f"Erro ao extrair campo '{field}': {message}")
        self.field = field


class BusinessRuleError(PokeCrawlerException):
    """Erro lançado quando os dados extraídos violam regras do domínio Pokémon."""
    def __init__(self, field: str, message: str):
        super().__init__(f"Violação de regra no campo '{field}': {message}")
        self.field = field


class DatabaseError(PokeCrawlerException):
    """Erro base para operações de banco de dados."""
    pass


class DuplicatePokemonError(DatabaseError):
    """Erro lançado quando se tenta inserir um Pokémon já existente."""
    pass
