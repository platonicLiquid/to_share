def main():
    #setting imports
    from html import parser
    import requests
    from lxml import html
    from requests.sessions import session
    import requests_html
    from requests_html import HTMLSession
    from html.parser import HTMLParser

    #setting variables
    error_messages = []
    logger = []
    confluence_core_link = 'https://analytics.kp.org'
    confluence_view_source_link = 'https://analytics.kp.org/confluence/plugins/viewsource/viewpagesrc.action?pageId='

    metrics_pageID = str(70094946)

    page_tree_builder = '/confluence/plugins/pagetree/naturalchildren.action?' +\
        'excerpt=false&' +\
        'sort=position&' +\
        'disableLinks=false&' +\
        'expandCurrent=false&' +\
        'hasRoot=true&' +\
        'pageId=' + metrics_pageID + '&' +\
        'startDepth=20&'


    #this class creates a parser object. It is used to get the attribute data of an element on the webpage with
    #the tag name 'description-tag-name'
    class Parser(HTMLParser):
        return_attrs = None

        def handle_starttag(self, tag: str, attrs):
            if tag == 'description-tag-name':
                self.return_attrs = attrs

    #this function returns an html response object. It is used for being able to search through the html to find various tags.
    def HTMLsession_getter(link_input):
        try:
            session = HTMLSession()
            response = session.get(link_input)
        except requests.exceptions.RequestException as e:
            print(e)
            error_messages.append([link_input, e])
        return(response)

    #this function returns a response object. It is used for the initial grabbing of the page
    def session_getter(link_input):
        with requests.Session() as ses:
            try:
                response = ses.get(link_input, timeout = None)
            except requests.exceptions.RequestException as e:
                error_messages.append(e)
                return('', '', error_messages)
        return(response)



    response = session_getter(confluence_core_link + page_tree_builder)
    logger.append('Successfully got link page.')
    try:
        webpage = html.fromstring(response.content)
    except Exception as e:
        error_messages.append(e)
        return('', '', error_messages)

    links_list = webpage.xpath('//a/@href')
    logger.append('Successfuly got links.')

    del response, webpage

    parser = Parser()

    dictionary_return = {}

    #due to a bug with how confluence is returning the http request, we have to grab the html, fix it, and then reparse the fixed html.
    for link in links_list:
        if link != '#':
            response = HTMLsession_getter(confluence_core_link + link)
            meta_list = response.html.find('meta')
            for element in meta_list:
                try:
                    if 'ajs-page-id' in element.attrs['name']:
                        page_id = element.attrs['content']
                        break
                except:
                    next
            response = session_getter(confluence_view_source_link + str(page_id))
            html_to_clean = str(response.content)
            cleaned_html = html_to_clean.replace('&lt;', '<').replace('\\n', '')
            #check if tag to scrape is on page, else skip to next confluence page
            if 'description-tag-name' not in cleaned_html:
                continue
            parser.feed(cleaned_html)
            result = parser.return_attrs
            print(result)
            confluence_definition = None
            confluence_measure_name = None
            #scrape values off web page, break loop if there are any errors and return errors, else append scraped values to list
            if result != None:
                for element in result:
                    logger.append(element)
                    if len(element) > 3:
                        logger.append('Length Error at ' + str(page_id))
                    if 'value' in element:
                        confluence_definition = element[1]
                        print(confluence_definition)
                    elif 'id' in element:
                        confluence_measure_name = element[1]
                        print(confluence_measure_name)
                try:
                    if confluence_definition != None or confluence_measure_name != None:
                        dictionary_return[page_id] = [confluence_definition, confluence_measure_name]
                except Exception as e:
                    error_message = 'Error at pageID = ' + str(page_id)
                    error_messages.append(error_message)
                    return('', logger, error_messages)
    #create a list with a header, append items to list, and return list
    list_return = [['ConfluencePageID', 'ConfluenceMeasureDefinition', 'ConfluenceMeasureName']]
    for key in dictionary_return:
         list_return.append([key, dictionary_return[key][0].replace('\\', ''), dictionary_return[key][1]])

    return(list_return, logger, error_messages)


if __name__ == '__main__':
    main()
