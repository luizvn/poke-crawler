from lxml import html, etree
import logging
import re
from typing import Dict, Any, Optional, List

from src.core.config import settings
from src.core.exceptions import BusinessRuleError, FieldExtractionError


logger = logging.getLogger(__name__)


def extract_image_url(html_content: str) -> Optional[str]:
    """Interface pública para extração da imagem."""
    tree = html.fromstring(html_content)
    base_name = _get_base_name(tree)

    return _extract_image_url(tree, base_name)


def _is_pokemon_page(tree: etree._Element) -> bool:
    """Verifica se a página é de 'não encontrado'."""

    if tree.xpath('//div[contains(@class, "noarticletext")]'):
        return False

    return True


def parse_pokemon(html_content: str) -> Dict[str, Any]:
    """Orquestra o parsing do HTML para a Forma Base com validações."""
    tree = html.fromstring(html_content)

    if not _is_pokemon_page(tree):
        raise FieldExtractionError("name", "O termo fornecido não corresponde a um Pokémon válido na Bulbapedia.")

    base_name = _get_base_name(tree)
    if not base_name:
        raise FieldExtractionError("name", "Título da página não encontrado ou inválido.")

    data = {}
    data.update(_extract_identity(tree, base_name))

    types = _extract_types(tree, base_name)
    if not types:
        raise FieldExtractionError("types", "Nenhum tipo encontrado para a forma base.")

    if len(types) > settings.MAX_TYPES:
        raise BusinessRuleError("types", f"Foram encontrados mais de {settings.MAX_TYPES} para esse pokémon.")
    data["types"] = types

    data.update(_extract_stats(tree))

    data["evolution"] = _extract_evolutions(tree, base_name)

    abilities = _extract_abilities(tree, base_name)
    if not abilities:
        raise FieldExtractionError("abilities", "Tabela de habilidades não encontrada ou vazia.")

    if len(abilities) > settings.MAX_ABILITIES:
        raise BusinessRuleError("abilities", f"Foram encontradas mais de {settings.MAX_ABILITIES} abilidades. ")
    data["abilities"] = abilities

    data["image_url"] = _extract_image_url(tree, base_name)

    return data


def _get_base_name(tree: etree._Element) -> str:
    """Extrai o nome base do Pokémon."""
    title_texts = tree.xpath('//h1[@id="firstHeading"]//text()')
    return "".join(title_texts).replace("(Pokémon)", "").strip()


def _extract_identity(tree: etree._Element, base_name: str) -> Dict[str, Any]:
    """Extrai Nome, Número e Categoria de forma estrita."""
    data = {"name": base_name}

    # POKÉDEX_NUMBER
    pokedex_elements = tree.xpath('//a[@title="List of Pokémon by National Pokédex number"]//text()')
    number = next((text for text in pokedex_elements if "#" in text), None)
    if not number:
        raise FieldExtractionError("pokedex_number", "Número da Pokédex não encontrado.")
    data["pokedex_number"] = number.replace("#", "").strip()

    # CATEGORY
    category_link = tree.xpath('//a[@title="Pokémon category"]')
    if not category_link:
        raise FieldExtractionError("category", "Link de categoria não encontrado.")

    explains = category_link[0].xpath('.//span[@class="explain"]')
    if explains:
        base_explain = None
        for exp in explains:
            if (exp.get("title") or "").lower() == base_name.lower():
                base_explain = exp
                break
        if base_explain is None:
            base_explain = explains[0]

        category_clean = ((base_explain.text or "") + (base_explain.tail or "")).strip()
    else:
        category_elements = category_link[0].xpath('.//text()')
        category_clean = "".join(category_elements).replace("Pokémon category", "").strip()

    if not category_clean:
        raise FieldExtractionError("category", "Texto da categoria está vazio.")

    data["category"] = category_clean
    return data


def _extract_types(tree: etree._Element, base_name: str) -> List[str]:
    """Extrai os tipos filtrando pela forma base."""
    type_columns = tree.xpath(
        '//a[@title="Type"]/ancestor::td[1]//table[contains(@class, "roundy")]//tr[1]/td[not(contains(@style, "display: none"))]')

    if not type_columns:
        return []

    valid_types = []
    for col in type_columns:
        small_texts = col.xpath('.//small//text()')
        form_text = "".join(small_texts).strip().lower()
        if not form_text or form_text == base_name.lower():
            raw_types = col.xpath('.//b/text()')
            valid_types = [t.strip() for t in raw_types if t.strip() and t.strip() != "Unknown"]
            if valid_types: break

    if not valid_types:
        raw_types = type_columns[0].xpath('.//b/text()')
        valid_types = [t.strip() for t in raw_types if t.strip() and t.strip() != "Unknown"]

    return list(dict.fromkeys(valid_types))


def _extract_stats(tree: etree._Element) -> Dict[str, str]:
    """Extrai os stats de forma estrita."""
    target_table_xpath = (
        '//span[@id="Base_stats"]/ancestor::*[self::h3 or self::h4]'
        '/following-sibling::*[self::h5 or self::h6][span[contains(@id, "onward")]][1]'
        '/following-sibling::table[1]'
    )
    tables = tree.xpath(target_table_xpath)

    if not tables:
        tables = tree.xpath('(//span[@id="Base_stats"]/ancestor::*[self::h3 or self::h4]/following-sibling::table)[1]')

    if not tables:
        raise FieldExtractionError("stats", "Tabela de stats não encontrada.")

    target_table = tables[0]

    def get_val(stat_name: str, title: str = "Stat") -> str:
        query = f'.//a[@title="{title}" and .//text()="{stat_name}"]/parent::div/following-sibling::div/text()'
        result = target_table.xpath(query)
        if not result or not result[0].strip().isdigit():
            raise FieldExtractionError(stat_name.lower().replace(".", ""),f"Stat {stat_name} não encontrado ou inválido.")
        return result[0].strip()

    hp_query = './/a[@title="HP" and .//text()="HP"]/parent::div/following-sibling::div/text()'
    hp_res = target_table.xpath(hp_query)
    if not hp_res or not hp_res[0].strip().isdigit():
        raise FieldExtractionError("hp", "Stat HP não encontrado ou inválido.")

    return {
        "hp": hp_res[0].strip(),
        "attack": get_val("Attack"),
        "defense": get_val("Defense"),
        "sp_atk": get_val("Sp. Atk"),
        "sp_def": get_val("Sp. Def"),
        "speed": get_val("Speed")
    }


def _extract_abilities(tree: etree._Element, base_name: str) -> List[Dict[str, Any]]:
    """Extrai habilidades."""
    abilities = []
    table = tree.xpath('//a[@title="Ability"]/ancestor::td[1]//table[contains(@class, "roundy")]')
    if not table: return []

    base_name_lower = base_name.lower()
    visible_tds = table[0].xpath('.//td[not(contains(@style, "display: none"))]')

    for td in visible_tds:
        full_text = "".join(td.xpath('.//text()')).lower()

        if "hidden ability" in full_text:
            small_text = "".join(td.xpath('.//small//text()')).lower()
            forms_str = small_text.replace("hidden ability", "").strip()
            forms_list = [f.strip() for f in re.split(r'and|,|&|\n', forms_str) if f.strip()]

            if not forms_list or any(f == base_name_lower for f in forms_list):
                nodes = td.xpath('.//a[contains(@title, "(Ability)")]//text()')
                for a in nodes:
                    if a.strip(): abilities.append({"name": a.strip(), "is_hidden": True})
        else:
            td_small_texts = [t.lower().strip(" ()") for t in td.xpath('.//small//text()') if t.strip()]

            if td_small_texts and base_name_lower not in td_small_texts:
                continue

            html_str = etree.tostring(td, encoding='unicode', method='html')
            chunks = re.split(r'<br\s*/?>', html_str, flags=re.IGNORECASE)
            for chunk in chunks:
                c_tree = html.fromstring(f"<div>{chunk}</div>")
                small = "".join(c_tree.xpath('.//small//text()')).lower().strip(" ()")
                if not small or small == base_name_lower:
                    nodes = c_tree.xpath('.//a[contains(@title, "(Ability)")]//text()')
                    for a in nodes:
                        if a.strip(): abilities.append({"name": a.strip(), "is_hidden": False})
                    if nodes: break
    return abilities


def _extract_evolutions(tree: etree._Element, base_name: str) -> Dict[str, List[str]]:
    """Extrai sucessores e antecessores."""
    evo_data = {"predecessors": [], "successors": []}

    header = tree.xpath('//*[self::h2 or self::h3][@id="Evolution" or span[@id="Evolution"]]')
    if not header:
        return evo_data

    container = header[0].xpath('following-sibling::*[self::div or self::table][1]')
    if not container:
        return evo_data

    family_containers = container[0].xpath(
        './/*[contains(@style, "border: 3px solid") or contains(@style, "border:3px solid")]')

    if not family_containers:
        family_containers = [container[0]]

    target_container = family_containers[0]

    if len(family_containers) > 1:
        base_name_lower = base_name.lower()
        for fc in family_containers:
            title_nodes = fc.xpath('preceding-sibling::p[1]//b//text() | ancestor::div[1]/p/b/text()')
            if title_nodes:
                title = "".join(title_nodes).strip().lower()
                if title == base_name_lower:
                    target_container = fc
                    break

    evolution_tables = target_container.xpath(
        './/table[.//small[contains(text(), "Unevolved") or contains(text(), "Evolution") or contains(text(), "Baby")]]')

    if not evolution_tables:
        return evo_data

    stage_map = {}

    for table in evolution_tables:
        stages = table.xpath(
            './/small[contains(text(), "Unevolved") or contains(text(), "Evolution") or contains(text(), "Baby")]/text()')
        if not stages:
            continue
        name_nodes = table.xpath(
            './/a/span[contains(@style, "color:#000")]/text() | .//a[not(span) and not(contains(@class, "image"))]/text() | .//span[contains(@style, "color:#000")]/text()')
        valid_names = [n.strip() for n in name_nodes if n.strip() and n.strip().lower() != base_name.lower()]
        if valid_names and stages:
            p_name = valid_names[0]
        else:
            self_link = table.xpath('.//a[contains(@class, "selflink")]')
            if self_link:
                p_name = base_name
            else:
                continue

        s_name = stages[0].strip()

        if s_name not in stage_map:
            stage_map[s_name] = []
        if p_name not in stage_map[s_name] and p_name != base_name:
            stage_map[s_name].append(p_name)
        elif p_name == base_name and base_name not in stage_map[s_name]:
            stage_map[s_name].append(p_name)

    RANK = {"baby pokémon": 1, "unevolved": 2, "first evolution": 3, "second evolution": 4}
    ordered = sorted(stage_map.keys(), key=lambda k: RANK.get(k.lower(), 99))

    idx = -1
    for i, stage in enumerate(ordered):
        if base_name.lower() in [n.lower() for n in stage_map[stage]]:
            idx = i
            break

    if idx != -1:
        if idx > 0:
            evo_data["predecessors"] = [p for p in stage_map[ordered[idx - 1]] if p.lower() != base_name.lower()]
        if idx < len(ordered) - 1:
            evo_data["successors"] = [s for s in stage_map[ordered[idx + 1]] if s.lower() != base_name.lower()]

    return evo_data


def _extract_image_url(tree: etree._Element, base_name: str) -> Optional[str]:
    """Busca a imagem."""
    image_table = tree.xpath('//a[contains(text(), "Images on the Bulbagarden Archives")]/ancestor::table[1]')

    if image_table:
        cells = image_table[0].xpath('.//td[.//img]')
    else:
        cells = tree.xpath('//table[contains(@class, "roundy")]//td[.//img]')

    if not cells:
        return None

    base_name_lower = base_name.lower()

    for cell in cells:
        small_texts = [t.strip().lower() for t in cell.xpath('.//small//text()') if t.strip()]

        if not small_texts or base_name_lower in small_texts:
            src = cell.xpath('.//img/@src')
            if src:
                url = src[0]
                return "https:" + url if url.startswith("//") else url

    if image_table:
        src = cells[0].xpath('.//img/@src')
        if src:
            url = src[0]
            return "https:" + url if url.startswith("//") else url

    return None
