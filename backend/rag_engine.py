from langchain_community.document_loaders import UnstructuredURLLoader
urls = ['https://www.victoriaonmove.com.au/local-removalists.html','https://victoriaonmove.com.au/index.html','https://victoriaonmove.com.au/contact.html']
loader = UnstructuredURLLoader(urls=urls)
data = loader.load() 