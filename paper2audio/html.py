label2tag = {
    "Title": ("<h1 class='title'>", "</h1>"),
    "Text": ("<p class='text'>", "</p>"),
    "List-item": ("<p class='list-item'>", "</p>"),
    "Section-header": ("<h2 class='section-header'>", "</h2>"),
    "Caption": ("<p class='caption'>", "</p>"),
}

def text2html(parts):

    output = """
    <!DOCTYPE html>
    <html>
    <head>
    <link rel="stylesheet" href="https://unpkg.com/latex.css/style.min.css" />
    </head>
    <body>
    """
    
    for part in parts:
        tag = label2tag.get(part["label"], ("<p>", "</p>"))
        output += (f"{tag[0]}{part['text']}{tag[1]}\n")
    
    output += """
    </body>
    </html>
    """
    return output