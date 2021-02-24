from string import Template
import scrapper

jisho_template = Template("https://jisho.org/search/${text}")


def parse_jp(in_html):
    furigana = in_html.find('span',
                            {'class': 'japanese_word__furigana_wrapper'}
                            ).text.strip()
    text = in_html.find('span',
                        {'class': 'japanese_word__text_wrapper'}
                        ).text.strip()
    return f'<ruby><rb>{text}</rb><rt>{furigana}</rt></ruby>'


def get_ruby_html(line):
    if line.strip() == '':
        return line
    soup = scrapper.get_soup(jisho_template.substitute(text=line))
    if not soup:
        return line
    result = soup.find(id='zen_bar')
    if not result:
        return line
    outline = ''
    jisho_lines = result.find_all('ul', {'class': 'clearfix'})
    for jl in jisho_lines:
        texts = jl.find_all('li')
        for text in texts:
            outline += parse_jp(text)
    return outline


def jisho_html(infile, outfile, title='Rezero Arc7'):
    with open(infile) as reader:
        lines = map(get_ruby_html, reader)
        with open(outfile, 'w', encoding='utf-8') as writer:
            writer.write(f'<html><title>{title}</title><body>')
            for ln, line in enumerate(lines, start=1):
                print(f'LINE: {ln}')
                writer.write(f'<p>\n<sup>{ln}:</sup>\t{line}\n</p>\n')
            writer.write('</body></html>')


def main():
    chap = 510
    jisho_html(f'./data/n2267be_{chap}-jp.txt',
               f'./data/n2267be_{chap}-jp.html',
               title=f'Rezero Arc7 Chapter {chap-502}')


if __name__ == '__main__':
    main()
