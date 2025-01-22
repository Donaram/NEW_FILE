
import scrapy

class ShoespiderSpider(scrapy.Spider):
    name = "shoespider"
    allowed_domains = ["www.mytheresa.com"]
    start_urls = ["https://www.mytheresa.com/int/en/men/shoes?rdr=mag&page=1"]
    page_num = 2  # Start from page 2 since page 1 is in start_urls

    def parse(self, response):
        # Extract product elements from the current page
        shoes = response.css('div.item.item--sale')

        for shoe in shoes:
            # Extract price details from the main page
            prices = shoe.css('span.pricing__prices__price::text').getall()
            prices = [price.strip() for price in prices if price.strip()]  # Clean up the prices

            if len(prices) == 2:  # If both prices exist, the first is listing price, the second is discounted price
                listing_price = prices[0]
                discounted_price = prices[1]
            else:
                listing_price = prices[0] if prices else None
                discounted_price = None

            # Extract relative URL for the shoe's product page
            relative_url = shoe.css('a.item__link::attr(href)').get()
            shoe_url = response.urljoin(relative_url)

            # Follow the product page to scrape additional details
            yield response.follow(shoe_url, callback=self.parse_shoe_page, meta={
                'listing_price': listing_price,
                'discounted_price': discounted_price
            })

        # Handle pagination: Increment the page number for the next page
        if self.page_num <= 100:
            next_page = f'https://www.mytheresa.com/int/en/men/shoes?rdr=mag&page={self.page_num}'
            self.page_num += 1  # Increment page number for the next request
            yield response.follow(next_page, callback=self.parse)

    def parse_shoe_page(self, response):
        # Retrieve the prices passed from the main page
        listing_price = response.meta.get('listing_price')
        discounted_price = response.meta.get('discounted_price')

        # Extract prices from the product page, if needed
        prices = response.css('span.pricing__prices__price::text').getall()
        filtered_prices = [price.strip() for price in prices if price.strip()]
        first_price = filtered_prices[0] if filtered_prices else None

        discounted_prices = response.css('span.pricing__prices__value--discount span.pricing__prices__price::text').getall()
        filtered_discounted_prices = [price.strip() for price in discounted_prices if price.strip()]
        first_discounted_price = filtered_discounted_prices[0] if filtered_discounted_prices else None

        # Yield the scraped data
        yield {
            "breadcrumb": response.css('div.breadcrumb__item a.breadcrumb__item__link::text').getall(),
            "image_url": response.css('img.product__gallery__carousel__image::attr(src)').get(),
            "brand": response.css('a.product__area__branding__designer__link::text').get(),
            "product_name": response.css('div.product__area__branding__name::text').get(),
            "listing_price": listing_price or first_price,  # Use the listing price from the main page or fallback to product page
            "offer_price": discounted_price or first_discounted_price,  # Use the discounted price from the main page or fallback
            "discount": response.css('span.pricing__info__percentage::text').get(),
            "sizes": response.css('div.sizeitem span.sizeitem__label::text').getall(),
            "product_details": response.css('ul li::text').getall(),
            "URL": response.url,
        }

