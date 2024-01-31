from collect import ExternalPage
from analyze import load_formated_data
import requests
from bs4 import BeautifulSoup


def rename_wikiartcles_data(pages: list[ExternalPage]) -> list[ExternalPage]:
    result = [] 
    count = len(pages)
    for i, page in enumerate(pages):
        print(f"Processing: {i} / {count}")
        new_wikilinks = []
        for wikilink in page.wikilinks:
            res = requests.get(wikilink)
            if res.status_code != 200:
                continue
            soup = BeautifulSoup(res.text, 'html.parser')
            name = soup.find_all(class_="mw-page-title-main")
            if name is None or len(name) == 0:
                continue
            new_wikilinks.append(name[0].text)
        page.wikilinks = list(set(new_wikilinks))
        result.append(page)
    return result


if __name__ == '__main__':
    pages = load_formated_data("pagedata.txt")
    new_pages = rename_wikiartcles_data(pages)

    with open("processed_pagedata.txt", "w+", encoding='utf8') as fp:
        fp.write("\n".join([str(x) for x in new_pages if len(x.wikilinks) >= 0]))
