
import logging
import re
import os
from datetime import datetime, timedelta
import re
import time
from selenium.common.exceptions import NoSuchElementException

from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from colorama import Fore, Style  # ✅ Color output for keyword matches
from db.job_storage import JobStorage

logger = logging.getLogger(__name__)

def calculate_post_date(post_time):
    """
    Parses a string like '7 hours ago', '17 minutes ago', '4d', etc.,
    and returns the exact date as a string formatted as "%Y-%m-%d %H:%M:%S".
    """
    try:
        # Extended regex to handle both full words and abbreviations.
        match = re.match(
            r"(\d+)\s*(minute|minutes|min|m|hour|hours|hr|h|day|days|d|week|weeks|w)?(?:\s*ago)?",
            post_time,
            re.IGNORECASE
        )
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            # If no unit is provided, default to minutes.
            if not unit:
                unit = "minute"
            else:
                unit = unit.lower()

            now = datetime.now()
            if unit in ["minute", "minutes", "min", "m"]:
                post_date = now - timedelta(minutes=amount)
            elif unit in ["hour", "hours", "hr", "h"]:
                post_date = now - timedelta(hours=amount)
            elif unit in ["day", "days", "d"]:
                post_date = now - timedelta(days=amount)
            elif unit in ["week", "weeks", "w"]:
                post_date = now - timedelta(weeks=amount)
            else:
                return "Invalid Date"

            return post_date.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return "Invalid Date"
    except Exception as e:
        logger.error(f"❌ Error calculating post date: {e}")
        return "Invalid Date"

def clean_post_text(text):
    """
    Removes lines from the extracted post text that are likely irrelevant.
    Adjust the list of unwanted lines as needed.
    """
    unwanted_lines = {
        "…more",
        "Show translation",
        "Like",
        "Comment",
        "Repost",
        "Send"
    }
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip lines that exactly match any unwanted phrase.
        if stripped in unwanted_lines:
            continue
        # Optionally, skip very short lines.
        if len(stripped) < 2:
            continue
        cleaned_lines.append(stripped)
    return "\n".join(cleaned_lines)


class FeedScraper:
    """Scrolls through the LinkedIn feed and extracts posts containing specific keywords and links."""

    def __init__(self, driver, keywords=None, keywords_file="app/utils/keywords.txt"):
            self.driver = driver
            self.scrolled_posts = set()  # Store post identifiers instead of elements
            self.job_storage = JobStorage()  # ✅ Store job posts using JobStorage
            
            # ✅ Load keywords from file if none are provided
            if keywords is None or not keywords:
                self.keywords = self.load_keywords_from_file(keywords_file)
            else:
                self.keywords = keywords

    import os

    def load_keywords_from_file(self, file_path="app/utils/keywords.txt"):
        """Loads keywords from a text file, one per line, ensuring correct encoding and handling errors."""
        
        # Convert to a relative path from the script's directory
        relative_path = "app/utils/keywords.txt"

        if not os.path.exists(relative_path):
            logger.error(f"❌ Keywords file '{relative_path}' not found. Using an empty keyword list.")
            return []  # Return an empty list if the file is missing

        try:
            with open(relative_path, "r", encoding="utf-8") as f:
                keywords = [line.strip() for line in f if line.strip()]  # Remove empty lines

            if not keywords:
                logger.warning(f"⚠️ Loaded keywords file '{relative_path}', but it is empty.")

            logger.info(f"✅ Loaded {len(keywords)} keywords from '{relative_path}'")
            return keywords

        except Exception as e:
            logger.error(f"❌ Error reading keywords file '{relative_path}': {e}")
            return []


    def scroll_and_extract_posts(self, max_scrolls=5):
        """Scrolls through the LinkedIn feed and extracts only posts containing specific keywords."""
        logger.info("🔄 Starting to scroll through LinkedIn feed...")

        extracted_posts = []

        if not hasattr(self, 'seen_posts'):
            self.seen_posts = set()  # ✅ Ensure seen_posts persists between scrolls

        for scroll_count in range(max_scrolls):
            logger.info(f"📜 Scroll {scroll_count + 1}/{max_scrolls}...")

            # ✅ Get the current number of posts
            prev_post_count = len(self.driver.find_elements(By.CSS_SELECTOR, "div.feed-shared-update-v2"))
            prev_height = self.driver.execute_script("return document.body.scrollHeight")

            try:
                # ✅ Scroll and wait for new posts to load
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                WebDriverWait(self.driver, 15).until(
                    lambda driver: driver.execute_script("return document.body.scrollHeight") > prev_height
                )
            except TimeoutException:
                logger.info("🚧 No more new posts detected (page height did not increase). Stopping scroll.")
                break

            # ✅ Get updated post elements
            posts = self.driver.find_elements(By.CSS_SELECTOR, "div.feed-shared-update-v2")
            logger.info(f"🔍 Total posts found on page after scroll: {len(posts)}")

            new_posts = []
            for post in posts:
                try:
                    post_id = post.get_attribute("data-urn")
                    # ✅ Fallback if data-urn is missing
                    if not post_id:
                        post_id = hash(post.text)  # Unique fallback ID using post text
                    if post_id and post_id not in self.seen_posts:
                        new_posts.append(post)
                        self.seen_posts.add(post_id)  # ✅ Ensure post is marked as seen
                    else:
                        logger.debug(f"Skipping already seen post {post_id}")
                except StaleElementReferenceException:
                    logger.warning("⚠️ A post disappeared before it could be processed.")

            logger.info(f"🔍 Found {len(new_posts)} new posts in this scroll.")

            # ✅ Process new posts
            for index, post in enumerate(new_posts):
                try:
                    post_id = post.get_attribute("data-urn") or hash(post.text)
                    post_text_data = self.extract_post_text(post)
                    post_text = post_text_data.get("text", "No Text Found")
                    post_links = post_text_data.get("links", [])
                    post_emails = post_text_data.get("emails", [])

                    # ✅ Identify matching keywords
                    matching_keywords = [kw for kw in self.keywords if kw.lower() in post_text.lower()]
                    if matching_keywords:
                        logger.info(f"✅ Found keyword(s) {matching_keywords} in Post {index + 1} (ID: {post_id})!")
                    else:
                        logger.info(f"❌ Skipping Post {index + 1} (ID: {post_id}) - No matching keywords")
                        continue

                    post_data = self.extract_post_data(post)
                    if not post_data:
                        continue

                    publisher_url = self.extract_publisher_url(post)
                    post_time, post_date = self.extract_post_time(post)

                    # Save matching keywords as a comma-separated string in "keyword_found"
                    keyword_str = ", ".join(matching_keywords)

                    post_data.update({
                        "index": index + 1,
                        "post_publisher_url": publisher_url,
                        "post_time": post_time,
                        "post_date": post_date,
                        "post_id": post_id,
                        "post_links": post_links,
                        "post_emails": post_emails,
                        "keyword_found": keyword_str
                    })
                    extracted_posts.append(post_data)

                    # ✅ Save post immediately inside the loop
                    self.job_storage.save_job_posts_to_db([post_data])
                    logger.info(f"✅ Extracted & Saved Post {index + 1} (Post ID: {post_id}) with keywords: {matching_keywords}")

                except StaleElementReferenceException:
                    logger.warning("⚠️ A post disappeared before processing.")

        logger.info(f"✅ Total posts extracted: {len(extracted_posts)}")
        return extracted_posts


    
    def extract_post_data(self, post):
        """Extracts post text, links, and emails from a LinkedIn post."""
        try:
            post_text_data = self.extract_post_text(post)  # Extract text, links, emails
            return {
                "post_text": post_text_data["text"],
                "post_links": post_text_data["links"],
                "post_emails": post_text_data["emails"]
            }
        except Exception as e:
            logger.error(f"❌ Error extracting post data: {e}")
            return None
        
    def extract_publisher_url(self, post):
        """Extracts the original publisher's profile URL from the post."""
        try:
            # ✅ Try the most reliable method first
            try:
                publisher_element = post.find_element(By.CSS_SELECTOR, ".update-components-actor__container a")
                if publisher_element:
                    publisher_url = publisher_element.get_attribute("href")
                    if publisher_url:
                        return publisher_url
            except NoSuchElementException:
                logger.warning("⚠️ Could not find publisher using '.update-components-actor__container a'.")

            # ✅ Fallback in case the first method fails
            try:
                alternate_publisher = post.find_element(By.XPATH, ".//a[contains(@href, '/in/') or contains(@href, '/company/')]")
                if alternate_publisher:
                    publisher_url = alternate_publisher.get_attribute("href")
                    if publisher_url:
                        return publisher_url
            except NoSuchElementException:
                logger.warning("⚠️ Could not find publisher using alternative XPATH search.")

            logger.error("❌ Could not find publisher URL in post.")
            return "N/A"

        except Exception as e:
            logger.error(f"❌ Unexpected error extracting publisher URL: {e}")
            return "N/A"

        
    def clean_post_text(text):
            """
            Removes lines from the extracted post text that are likely irrelevant.
            Adjust the list of unwanted lines as needed.
            """
            unwanted_lines = {
                "…more",
                "Show translation",
                "Like",
                "Comment",
                "Repost",
                "Send"
            }
            lines = text.splitlines()
            cleaned_lines = []
            for line in lines:
                stripped = line.strip()
                # Skip lines that are exactly one of the unwanted phrases.
                if stripped in unwanted_lines:
                    continue
                # Optionally, skip very short lines or ones that are just numbers.
                if len(stripped) < 2:
                    continue
                cleaned_lines.append(stripped)
            return "\n".join(cleaned_lines)

    def extract_post_time(self, post):
        """
        Extracts the published time (e.g., '7 hours ago', '17 minutes ago')
        from a LinkedIn post and calculates the exact date.
        """
        try:
            post_time = "Unknown Time"
            post_date = None  # Will hold a datetime object if calculated

            try:
                # Execute JavaScript to extract the time from the given post
                post_time = self.driver.execute_script("""
                    function extractPublishedTime(post) {
                        if (!post) {
                            return "Post not found";
                        }
                        let timeElement = post.querySelector('.update-components-actor__sub-description .visually-hidden');
                        return timeElement ? timeElement.innerText.trim() : "Time not found";
                    }
                    return extractPublishedTime(arguments[0]);
                """, post)
                logger.info(f"✅ Extracted timestamp via JavaScript: {post_time}")
            except Exception as e:
                logger.warning(f"⚠️ Error extracting time via JavaScript: {e}")

            # Calculate the actual post_date using the local helper function.
            post_date_str = calculate_post_date(post_time)
            logger.info(f"✅ Calculated post date (pre-validation): {post_date_str}")

            # If the calculated post_date is a string, try to convert it to a datetime object.
            if isinstance(post_date_str, str) and post_date_str != "Invalid Date":
                try:
                    post_date = datetime.strptime(post_date_str, "%Y-%m-%d %H:%M:%S")
                    logger.info(f"✅ Parsed post date string to datetime: {post_date}")
                except Exception as parse_error:
                    logger.error(f"❌ Failed to parse post_date '{post_date_str}': {parse_error}")
                    post_date = None
            else:
                post_date = None

            return post_time, post_date

        except Exception as e:
            logger.error(f"❌ Failed to extract post time: {e}")
            return "Error", None



    
    def extract_links_from_post(self, post):
        """Extracts all href attributes from anchor tags within the post."""
        links = []
        try:
            anchor_elements = post.find_elements(By.TAG_NAME, "a")
            for a in anchor_elements:
                href = a.get_attribute("href")
                if href and href not in links:
                    links.append(href)
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
        return links

    def extract_post_text(self, post):
        """Extracts the full text content, links, and emails from a LinkedIn post.
        If the post text is truncated, attempts to click the 'see more' button to expand it."""
        try:
            post_text = "No Text Found"
            
            # Try primary method for text extraction.
            try:
                text_element = post.find_element(By.CSS_SELECTOR, ".feed-shared-update-v2__description")
                if text_element and text_element.text.strip():
                    post_text = text_element.text.strip()
            except NoSuchElementException:
                pass

            # Alternative extraction if primary fails.
            if post_text == "No Text Found":
                try:
                    alternative_text = post.find_element(By.CSS_SELECTOR, ".update-components-text-view span")
                    if alternative_text and alternative_text.text.strip():
                        post_text = alternative_text.text.strip()
                except NoSuchElementException:
                    pass  

            # If still not found, try to click "see more" then extract text via JavaScript.
            if post_text == "No Text Found":
                try:
                    more_button = post.find_element(By.CSS_SELECTOR, ".feed-shared-update-v2__see-more")
                    if more_button:
                        self.driver.execute_script("arguments[0].click();", more_button)
                        time.sleep(0.5)  # Wait for full text to load
                except NoSuchElementException:
                    pass
                post_text = self.driver.execute_script("return arguments[0].innerText.trim();", post)
                if not post_text:
                    post_text = "No Text Found"
            
            # Clean the extracted text.
            cleaned_text = clean_post_text(post_text)
            
            # Extract links using regex with \S+ and IGNORECASE flag.
            regex_links = re.findall(r'(https?://\S+)', post_text, re.IGNORECASE)
            tag_links = self.extract_links_from_post(post)
            combined_links = list(set(regex_links + tag_links))
            
            # Strip common trailing punctuation from each link.
            links = []
            emails_from_links = []
            for link in combined_links:
                link = link.strip(".,;:!?")
                if link.lower().startswith("mailto:"):
                    emails_from_links.append(link[len("mailto:"):])
                else:
                    links.append(link)
            
            # Extract emails from the text.
            extracted_emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', post_text)
            
            # Combine emails extracted from text and those found in links, deduplicating them.
            emails = list(set(extracted_emails + emails_from_links))
            
            return {"text": cleaned_text, "links": links, "emails": emails}
        except Exception as e:
            logger.error(f"❌ Error extracting post text: {e}")
            return {"text": "No Text Found", "links": [], "emails": []}



    

    def like_post(self, post):
        """Likes a LinkedIn post if it contains keywords."""
        try:
            like_button = post.find_element(By.XPATH, ".//button[contains(@aria-label, 'Like')]")
            if like_button:
                self.driver.execute_script("arguments[0].click();", like_button)
                logger.info("👍 Liked post successfully.")
            else:
                logger.warning("⚠️ Like button not found.")
        except NoSuchElementException:
            logger.error("❌ Could not find Like button.")


    