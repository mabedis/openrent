__author__ = "Alfin"
__copyright__ = ""
__maintainer__ = "Alfin"
__version__ = "0.1"

from .common_libraries import *
import re
import json
from decimal import Decimal
from re import sub


# from scrapy.loader.processors import TakeFirst, MapCompose, Join

class SpareroomSpider(scrapy.Spider):
    name = "openrent"

    # collection_name = 'london_properties_4June'

    def __init__(self, **kwargs):

        print("Key word args test ", kwargs)

        # Default Parameters ============================================================================

        self.iter = kwargs.get('iter')  # Default set to 1 Code parameter, Only from internal Codes
        if self.iter is None:
            self.iter = 1
        else:
            self.iter = int(self.iter)

        # -------------------------------------------------------------------------------------------------

        # User Input Parameters =========================================================================

        self.postal_code = kwargs.get('postal_code')  # Must
        self.property_for = kwargs.get('property_for')
        self.property_type = kwargs.get('property_type')
        self.beds = kwargs.get('beds')
        self.price_max = kwargs.get('price_max')
        self.keyword = kwargs.get('keyword')
        self.search_query = kwargs.get('search_query')
        # self.additional_property_type = kwargs.get('additional_property_type')
        # print("Any additional property type " , self.additional_property_type)

        # ------------------------------------------------------------------------------------------------

        # Site Search 1st URL Parameters =================================================================

        self.search_url = []
        self.search_string = ''
        add_postal_code = ''
        add_property_type = ''
        add_beds = ''
        add_price_max = ''
        add_keyword = ''

        property_search = ['']

        if self.postal_code is not None:
            add_postal_code = self.postal_code
        else:
            # Default
            add_postal_code = 'London'

        if self.property_for is not None:
            if 'sale' in self.property_for:
                # property_search = ['']
                add_property_type = ''
            elif 'rent' in self.property_for:
                add_property_type = ''

        if self.property_type is not None:
            if 'flat' in self.property_type:
                property_search = ['/flats']
            elif 'house' in self.property_type:
                property_search = ['/houses']
        else:
            # There are no extra parameters at the moment
            # Default
            property_search = ['']
            pass

        if self.beds is not None:
            add_beds = '&min_beds=' + str(self.beds)
        else:
            # Do not set any parameter for none
            pass

        if self.price_max is not None:
            add_price_max = '&max_rent=' + str(self.price_max)

        if self.keyword is not None:
            add_keyword = '&keyword=' + self.keyword

        self.search_string = add_postal_code + add_property_type + add_beds + add_price_max + add_keyword
        print(self.search_string)
        initail_site = ('https://www.openrent.co.uk/properties-to-rent/' + self.search_string + property_search[0])



        self.search_url.append('https://www.openrent.co.uk/properties-to-rent/' + self.search_string + property_search[0]
                               )

        # urls=['https://www.spareroom.co.uk/flatshare/search.pl?search='+ self.postal_code +'&flatshare_type='+self.share_type+'&location_type=area&action=search&submit=']

        # ------------------------------------------------------------------------------------------------

        self.urls = self.search_url
        #["https://www.openrent.co.uk/properties-to-rent/London"]
        print(" From openrent ", self.urls)

    def start_requests(self):
        print("test1")

        for url in self.urls:
            print("\n\n\ntest167", url)
            new_response = SplashRequest(url, self.search, endpoint='render.html', args={'wait': 1}, dont_filter=True)
            print ("test1333\n\n\n",new_response)
            yield SplashRequest(new_response.url, self.parse, endpoint='render.html', args={'wait': 1},
                                dont_filter=True)

    def search(self, response):
        print("test12")
        return scrapy.FormRequest.from_response(
            response,
            callback=self.parse
        )



    def parse(self, response):
        print("test1")

        print("\n\n\n\n current_page test", response.url)
        iter_new_page = False
        parsed = urlparse.urlparse(response.url)
        query_dict_set = urlparse.parse_qsl(parsed.query)
        new_parts = list(parsed)
        query_dict = {k: v for k, v in query_dict_set}
        current_page = 0
        if 'offset' in response.url:
            current_page = (int(query_dict['offset']) / 10) + 1
        else:
            current_page = 1

        query_dict['offset'] = int(current_page * 10)

        if ('search.pl' in response.url):
            sel_loc = response.xpath('//div[@class="search_form_matches"]//input/@value').extract()
            # print("Select Locations ",sel_loc)
            if len(sel_loc) > 0:
                iter_new_page = True
                query_dict['search'] = sel_loc[0]
                del query_dict['offset']

        new_parts[4] = urlparse.urlencode(query_dict)
        next_page_url = urlparse.unquote_plus(urlparse.urlunparse(new_parts))
        # print("Next Page full url" , next_page_url)
        print("current page test ", current_page)

        l = ItemLoader(item=RealEstateItem(), response=response)

        value_dict = {}

        if 'flatshare' in response.url:
            value_dict['property_for'] = 'rent'
        else:
            value_dict['property_for'] = ''

        source_ID = re.findall("var PROPERTYIDS =(.+?);\n", response.body.decode("utf-8"), re.S)
        ID_list = re.findall(r'\d+', source_ID[0])
        print("test print first property ID",ID_list[0], "total id's is", len(ID_list))

        value_dict['data_url'] = response.url
        value_dict['scrapped_date'] = datetime.today().strftime(DATE_FORMAT)
        value_dict['ref_site'] = 'open rent'
        value_dict['search_query'] = self.search_query
        print (value_dict['data_url'])
        ##reached source code.
        temp_store = []
        count1 = 0
        if len(ID_list) >=501:
            for id in ID_list:
                if count1 <= 4:
                    temp_store.append(id)
                    count1+=1
        else:
            for id in ID_list:
                temp_store.append(id)
        print("total property Id collected", len(temp_store))

        n = 30
        split_ID = [temp_store[i:i + n] for i in range(0, len(temp_store), n)]
        #print("splited ID",len(split_ID))
        url_list = []

        def url_from_id(prop_id):
            url = "https://www.openrent.co.uk/search/propertiesbyid?"
            for i in prop_id:
                url = url + '&ids=' + i
            return url
        for i in split_ID:
            temp = url_from_id(i)
            url_list.append(temp)
        print("url list", url_list)
        scrapped_data = l.load_item()
        global now
        expand_data = tuple(zip(*list(scrapped_data.values())))

        dict_data = dict(zip(scrapped_data.keys(), i))

        # yield SplashRequest(dict_data['detail_page_url'], callback=self.parse_details, endpoint='render.html',
        #                     args={'wait': 0.5}, dont_filter=True, meta={'item': dict_data}, )

        dict_data['detail_page_url'] = ['https://www.openrent.co.uk/search/propertiesbyid?&ids=1015302&ids=1057266&ids=1017632&ids=1075180&ids=1004607']
        url2scrap = dict_data.get('detail_page_url')
        for link in url2scrap:
            print("ride", type(dict_data), dict_data)
            print(link)
            yield SplashRequest(link,callback= self.request_data,method='GET',meta={'item': dict_data})
        print("test alfi")
        print(dict_data)
        print("sucess")

    def request_data(self, response):
        items_val = response.meta.get('item')
        print("\n\n\n\n response_page test", response.url)
        print("\n response1",items_val)
        read = requests.get(response.url)
        data = read.json()
        #print(data)
        #print(read.status_code)
        Id = []
        tittle = []
        for info in data:
            Id.append(info["id"])
            tittle.append(info["title"])
        #print(Id)
        #print(tittle)
        items_val['id'] = Id
        items_val['tittle'] = tittle
        yield items_val


        #https://www.openrent.co.uk/property-to-rent/london/Room-in-a-Shared-House-London-N15/1015302
        #https://www.openrent.co.uk/property-to-rent/london/Room-in-a-Shared-Flat/1057266






