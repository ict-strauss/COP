from xml.etree import ElementTree

class CGConfiguration:

    def __init__(self, filename):
        self.document = ElementTree.parse(filename)
        root = self.document.getroot()
        tag = self.document.find('CORS')
        self.isCORS = "yes" in tag.attrib['enable']
        self.url=tag.attrib['url']