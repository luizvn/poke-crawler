# PokéCrawler

PokéCrawler é uma API construída com **FastAPI** e **Playwright** projetada para extrair dados detalhados de Pokémon diretamente da Bulbapedia. O projeto foca em normalização de dados, persistência assíncrona e uma interface REST.

## Tecnologias e Escolhas Técnicas

- **FastAPI**: Escolhido pela performance e conhecimento prévio com o framework e suporte nativo a asyncio, essencial para operações de I/O intensivo.
- **Playwright**: Utilizado para o fetching das páginas. O Playwright permite lidar com conteúdos carregados dinamicamente.
- **SeleniumBase**: Integrado principalmente para gerenciar o contexto do navegador via **CDP (Chrome DevTools Protocol) Driver**. Essa abordagem é utilizada para melhorar a inicialização do browser, permitindo contornar a Cloudflare com mais sucesso.
- **lxml**: A biblioteca usada para o parsing do HTML. Foi escolhida pela sua performance, permitindo uma navegação precisa pela estrutura das páginas da Bulbapedia.
- **SQLAlchemy (aiosqlite)**: 
 Provedor de ORM assíncrono para garantir que as operações de banco de dados não bloqueiem o loop de eventos da API.
- **Pydantic**: Utilizado para validação dos dados extraídos e definição dos schemas da API.

---

## Instalação e Setup

### Pré-requisitos
- Python 3.14+
- Poetry

### Passo a Passo

1. **Instale as dependências:**
   ```bash
   poetry install
   ```

2. **Instale o binário do Chromium:**
   O Playwright precisa do Chromium para funcionar. Execute:
   ```bash
   poetry run playwright install chromium
   ```

3. **Configure o ambiente:**
   Renomeie o `.env.example` para `.env` e ajuste as variáveis se necessário.

4. **Inicie a API:**
   ```bash
   poetry run uvicorn src.main:app --reload
   ```

---

## Disclaimers e Observações

### 1. Nomes Especiais e Requisitos de Busca
Para Pokémons com nomes que possuem caracteres especiais ou pontuação, **é necessário enviar o nome exato** para que o crawler localize a página corretamente:
- **Símbolos de Gênero**: Use `Nidoran♀` ou `Nidoran♂`. O envio de apenas "Nidoran" resultará em erro ou página de desambiguação.
- **Pontuação**: Pokémons como `Mr. Mime` ou `Mime Jr.` **exigem** o ponto final e o espaço correto. O envio de "mr mime" (sem ponto) não será encontrado.
- Em caso de dúvida, o nome enviado deve ser exatamente o que aparece no título da página da Bulbapedia.

### 2. Redirects
Graças ao sistema de redirecionamento da Bulbapedia, a API aceita:
- Nomes com **acentuação** (ex: `Flabébé`).
- Nomes em **letras minúsculas** (ex: `pikachu`).
- O crawler seguirá o redirecionamento automático para a página correta do Pokémon.

### 3. Escopo: Apenas Formas Base
Atualmente, o PokéCrawler foca exclusivamente na **forma base** de cada Pokémon. 
- **Não há suporte** para Formas Regionais (ex: Alolan Vulpix).
- **Não há suporte** para variações de forma (ex: Formas do Rotom, Mega Evoluções ou Gigantamax).
Os dados extraídos (Stats, Tipos, etc.) serão sempre referentes à forma padrão da espécie.

### 4. Resposta Multi-Status (207)
Ao realizar o crawling de uma lista, a API retornará o status `207`. Isso significa que a operação foi concluída, mas você deve verificar o corpo da resposta para identificar quais Pokémon foram processados com sucesso e quais falharam (por exemplo, por nome inexistente).

---

## Testes
Para rodar a suíte de testes unitários e de integração:
```bash
poetry run pytest
```

