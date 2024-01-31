import grequests
import requests
from dataclasses import dataclass
from typing import Optional
from bs4 import BeautifulSoup
from collections import deque


WIKI_BASE = "https://pl.wikipedia.org/wiki/"  
PREFIX_LEN = len("https://")
SEEDS = ["Politechnika_Wrocławska"]
WIKI_PAGE_COUNT = 150
MAX_PAGES = 1000000


@dataclass
class WikiPage:
    name: str
    page_id: int
    wikipages: list[str]
    external_links: list[str]


@dataclass
class ExternalPage:
    name: str
    wikilinks: list[str]


def get_external(page: str) -> list[str]: 
    external_address = f"https://pl.wikipedia.org/w/api.php?action=parse&page={page}&prop=externallinks&format=json"
    res = requests.get(external_address)        
    json_data = res.json()
    external_links = []
    if res.status_code == 200 and 'parse' in json_data:
        external_links = json_data['parse']['externallinks']
    return external_links


def get_wikipage_data(page: str) -> Optional[WikiPage]:
    refernce_address = f"https://pl.wikipedia.org/w/api.php?action=parse&page={page}&prop=links&format=json"
    res = requests.get(refernce_address)

    if res.status_code != 200:
        return None

    json_data = res.json()

    if 'error' in json_data.keys():
        return None
    
    internal_links = [
        info['*'] for info in json_data["parse"]["links"]
        if info['ns'] == 0 # namespace for articles
    ]
    external_links = get_external(page)   
    return WikiPage(json_data['parse']['title'], json_data['parse']['pageid'], internal_links, external_links)
            

def get_external_page_data(page: str) -> Optional[ExternalPage]:
    if 'pdf' in page:
        return None

    res = requests.get(page, timeout=3)
    if res.status_code != 200:
        return None
    soup = BeautifulSoup(res.text, 'html.parser')
    links = [
        non_empty_link for link in soup.find_all('a')
        if (non_empty_link := link.get('href')) 
        and len(non_empty_link) > PREFIX_LEN
        and non_empty_link.startswith(WIKI_BASE)
    ]

    return ExternalPage(page, links)


def save_data(wikidata: list[WikiPage], extdata: list[ExternalPage]):
    with open("wikidata.txt", "w+", encoding='utf-8') as fp:
        fp.write("\n".join([str(x) for x in wikidata]))

    with open('pagedata.txt', 'w+', encoding='utf-8') as fp:
        fp.write('\n'.join([str(x) for x in extdata]))


def analyze_wiki() -> tuple[list[WikiPage], list[str]]:
    queue = deque()
    external_pages = []
    wikis = []

    for seed in SEEDS:
        queue.append(seed)

    visited = set()
    site_counter = 0
    while site_counter < WIKI_PAGE_COUNT:
        page = queue.popleft()
        if page in visited:
            continue

        wikidata = get_wikipage_data(page)
        if wikidata is None:
            continue

        visited.add(wikidata.name)
        site_counter += 1
        print(f'Analyzing wiki {site_counter}/{WIKI_PAGE_COUNT}: {page}')

        external_pages.extend(wikidata.external_links)
        queue.extend(wikidata.wikipages)
        wikis.append(wikidata)
    return wikis, external_pages


def analyze_pages(pages: set[str]) -> list[ExternalPage]:
    result = []
    count = len(pages)
    for i, page in enumerate(pages):
        if i >= MAX_PAGES:
            break

        print(f'Analyzing page {i}/{count}: {page}')

        try:
            data = get_external_page_data(page)
        except Exception as e:
            print(f"Parsing error: {page}\n Exception: {e}")
            continue

        if data is None:
            continue

        result.append(data)
    return result


def handle_fail(req, exc):
    # print(f"Parsing error: {page}\n Exception: {e}")
    pass

def process_async_req(res, page) -> Optional[ExternalPage]:
    soup = BeautifulSoup(res.text, 'html.parser')
    links = [
        non_empty_link for link in soup.find_all('a')
        if (non_empty_link := link.get('href')) 
        and len(non_empty_link) > PREFIX_LEN
        and non_empty_link.startswith(WIKI_BASE)
    ]
    return ExternalPage(page, links)

def process_wrapper(res, page) -> Optional[ExternalPage]:
    try:
        val = process_async_req(res, page)
    except:
        print("Some exception occured")
        return None
    return val

def async_analyze_pages(pages: set[str]) -> list[ExternalPage]:
    MAX_CONNECTIONS = 200
    PROBLEMATIC_EXTENSIONS = ['.pdf', '.xlsx', '.zip']
    urls = list(pages)
    result = []
    i = 0
    
    print("Collected pages: ", res_count := len(urls))
    for j in range(1, len(urls) + 1, MAX_CONNECTIONS):
        rs = (grequests.get(page, timeout=3, stream=False) for page in urls[j:j+MAX_CONNECTIONS])
        responses = grequests.map(rs, exception_handler=handle_fail)
        for res, page in zip(responses, urls[j:j+MAX_CONNECTIONS]):
            i += 1
            if res is None or res.status_code != 200:
                continue
            print(f"Parsing {i} / {res_count}: {page}")
            if any([page.endswith(ext) for ext in PROBLEMATIC_EXTENSIONS]):
                continue

            data = process_wrapper(res, page) 
            if data is not None:
                result.append(data)
            res.close()
    return result 


if __name__ == '__main__':
    wiki_data, page_adresses = analyze_wiki()
    external_data = async_analyze_pages(set(page_adresses))
    save_data(wiki_data, external_data)
