from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from api.tools.supabase_functions import get_authenticated_client


def get_lexile_by_isbn(isbn: str) -> str:

    """
    Given an ISBN, go to the Lexile page and return the Lexile measure (e.g. '770L').
    If no measure is found, returns None.
    """

    # Construct the Lexile book details URL
    url = f"https://hub.lexile.com/find-a-book/details/{isbn}/"

    # Set up Chrome WebDriver in headless mode
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(url)

        # Wait for the element with class 'lexile-measure'
        p_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.lexile-measure p[aria-hidden='true']"))
        )

        # p_element = driver.find_element(By.CSS_SELECTOR, "div.lexile-measure p[aria-hidden='true']")

        # Extract the Lexile measure text

        age_range = "N/A"

        # if we have a p_element (lexile score), we can also try to get the age range
        if p_element:

            dt_element = driver.find_element(By.XPATH, '//dt[contains(text(), "Age Range")]')
            dd_element = dt_element.find_element(By.XPATH, 'following-sibling::dd[1]')
            age_range = dd_element.text.strip()

        return p_element.text.strip(), age_range

    except Exception as e:
        print(f"Could not retrieve Lexile for ISBN {isbn}: {e}")
        return None, None

    finally:
        driver.quit()


# function to access books table in supabase - get isbn of each record
# send isbn to get_lexile_by_isbn
# update the record with the lexile measure
def update_books_with_lexile(supabase_client):

    """
    Fetch all books from the Supabase database, retrieve their Lexile measures,
    and update the records with the Lexile measure.
    """

    books = supabase_client.table('books').select('book_id, isbn').execute().data

    for book in books:
        isbn = book['isbn']
        lexile_measure, age_range = get_lexile_by_isbn(isbn)
        if lexile_measure:

            # Update the book record with the Lexile measure
            supabase_client.table('books').update({'lexile_measure': lexile_measure}).eq('book_id', book['book_id']).execute()

            # Optionally, you can also update the age range if needed
            supabase_client.table('books').update({'age_range': age_range}).eq('book_id', book['book_id']).execute()

            print(f"Updated ISBN {isbn} with Lexile measure {lexile_measure}")

        else:
            print(f"No Lexile measure found for ISBN {isbn}")

# Code	Meaning	Book information	Example	Lexile measure
# AD	Adult-directed	Picture books that are usually read to a child	Maurice Sendak's Where the Wild Things Are	AD740L
# NC	Non-Conforming	Books with a Lexile measure markedly higher than is typical for the publisher's intended audience	Seymour Simon's Amazing Aircraft	NC710L
# HL	High-Low	Books with a Lexile measure much lower than the average reading ability of the intended age range of its readers	Beth Goobie's Sticks and Stones	HL430L
# IG	Illustrated guide	Books that consist of independent pieces or sections of text that could be moved around without affecting the overall linear flow of the book	Dr. Gerald Legg's Birds of Prey	IG320L
# GN	Graphic novel	Graphic novel or comic book where the majority of the text appears as voice in thought bubbles	Siena Cherson Siegel's To Dance: A Ballerina's Graphic Novel	GN610L
# BR	Beginning reader	Books or readers with a Lexile measure below 0L	Don Curry's Fall Leaves	BR20L
# NP	Non-prose	Book comprising more than 50% non-standard or non-conforming prose, whose text cannot be assigned a Lexile measure	Maurice Sendak's Alligators All Around	NP


if __name__ == "__main__":

    # Example usage:
    # isbn = "9781911171195"
    # isbn = "9780590060196"
    # lexile = get_lexile_by_isbn(isbn)
    # print(f"Lexile for ISBN {isbn}: {lexile}")

    supabase_client = get_authenticated_client()

    # sign-in to supabase
    supabase_client.auth.sign_in_with_password({'email': 'test_password@testemail.com', 'password': 'test_password'})

    update_books_with_lexile(supabase_client)  # Assuming supabase_client is defined
