from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def download_gutenberg_book(author: str, title: str, output_file: str):

    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    try:
        # Step 1: Go to Gutenberg search page
        driver.get("https://www.gutenberg.org/ebooks/")

        # Step 2: Fill in title and author
        title_field = wait.until(EC.presence_of_element_located((By.NAME, "title")))
        author_field = wait.until(EC.presence_of_element_located((By.NAME, "author")))

        title_field.send_keys(title)
        author_field.send_keys(author)
        author_field.send_keys(Keys.RETURN)  # Submit search

        # remove stop words

        p_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "Frank"))
        )

        results = driver.find_elements(By.PARTIAL_LINK_TEXT, "Frank")

        results[0].click()  # Click the first result

        # Step 4: Click "Read this book online: HTML" (Read Now!)
        read_now_btn = wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Read this book online: HTML")))
        read_now_btn.click()

        # Step 5: Extract text
        time.sleep(3)  # Let page load fully
        book_text = driver.page_source

        # Strip out HTML tags? For now just save raw
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(book_text)

        print(f"Book saved to {output_file}")

    except Exception as e:
        print("Error:", e)

    finally:
        driver.quit()


if __name__ == "__main__":

    # Example usage:
    download_gutenberg_book(author="Mary Shelley", title="Frankenstein", output_file="frankenstein.txt")
