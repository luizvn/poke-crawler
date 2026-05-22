import asyncio
import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

from seleniumbase import cdp_driver
from playwright.async_api import async_playwright, Error as PlaywrightError, Page, Browser
from src.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PokemonFetcher:
    def __init__(self, browser: Browser, page: Page, driver):
        self.browser = browser
        self.page = page
        self.driver = driver

    async def fetch_html(self, pokemon_name: str, max_retries: Optional[int] = None) -> Optional[str]:
        if max_retries is None:
            max_retries = settings.MAX_RETRIES
            
        url = f"{settings.BASE_URL}{pokemon_name}{settings.URL_SUFFIX}"

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Acessando {url} (Tentativa {attempt})")
                await self.page.goto(url, wait_until="domcontentloaded")

                for _ in range(30):
                    html_content = ""
                    try:
                        html_content = await self.page.content()
                    except PlaywrightError as e:
                        if "navigating" in str(e):
                            logger.info("Página recarregando...")
                            await asyncio.sleep(1)
                            continue
                        else:
                            raise

                    if "mw-content-text" in html_content and "table" in html_content:
                        logger.info("Sucesso!")
                        await self.page.mouse.wheel(0, 500)
                        await asyncio.sleep(1)
                        return await self.page.content()

                    if "challenge-running" in html_content or "Just a moment" in html_content:
                        logger.info("Cloudflare na tela.")
                        try:
                            cf_frame = self.page.frame_locator("iframe[src*='cloudflare']").first
                            await cf_frame.locator("body").click(timeout=1000)
                        except Exception:
                            pass
                        await asyncio.sleep(1.5)
                    else:
                        await asyncio.sleep(1)

                logger.warning(f"Tentativa {attempt} falhou.")

            except Exception as e:
                logger.error(f"Erro no fluxo da Tentativa {attempt}: {e}")

        return None

    async def download_image(self, url: str, pokemon_name: str) -> Optional[str]:
        """Baixa a imagem usando o contexto do browser para evitar 403 (Cloudflare)."""

        save_dir = settings.BASE_DIR / settings.IMAGES_PATH
        save_dir.mkdir(parents=True, exist_ok=True)

        safe_name = pokemon_name.split('(')[0].strip().lower()
        filename = f"{safe_name}.png"
        file_path = save_dir / filename

        try:
            logger.info(f"Baixando imagem de {url} para {file_path}")
            response = await self.page.context.request.get(url)
            
            if response.status == 200:
                body = await response.body()
                with open(file_path, "wb") as f:
                    f.write(body)

                return str(file_path.relative_to(settings.BASE_DIR))
            else:
                logger.warning(f"Falha ao baixar imagem: Status {response.status}")
        except Exception as e:
            logger.error(f"Erro ao baixar imagem para {pokemon_name}: {e}")
        
        return None


@asynccontextmanager
async def get_browser_session() -> AsyncGenerator[PokemonFetcher, None]:
    async with async_playwright() as p:
        chromium_path = p.chromium.executable_path
        locale_args = ['--lang=en-US', '--accept-lang=en-US,en']

        logger.info("Iniciando Chromium via SeleniumBase...")
        driver = await cdp_driver.start_async(
            browser_executable_path=chromium_path,
            headless=settings.BROWSER_HEADLESS,
            ad_block=True,
            args=locale_args
        )

        endpoint_url = driver.get_endpoint_url()
        browser = await p.chromium.connect_over_cdp(endpoint_url)
        
        try:
            context = browser.contexts[0]
            page = context.pages[0]
            yield PokemonFetcher(browser, page, driver)
        finally:
            logger.info("Fechando sessão do navegador...")
            if browser and browser.is_connected():
                await browser.close()
            try:
                if hasattr(driver, "quit"):
                    driver.quit()
            except:
                pass
            await asyncio.sleep(0.25)
