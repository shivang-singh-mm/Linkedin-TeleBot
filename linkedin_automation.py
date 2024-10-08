from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.select import Select
import time
import csv
import os


def setup_driver():
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    return webdriver.Chrome(options=chrome_options)


def add_cookies(driver, cookies):
    driver.get("https://www.linkedin.com")
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get("https://www.linkedin.com/jobs/")
    time.sleep(5)


def search_jobs(driver, search_keyword):
    keyword_search = driver.find_element(By.CLASS_NAME, "jobs-search-box__text-input")
    keyword_search.click()
    keyword_search.send_keys(f"{search_keyword}", Keys.ENTER)
    time.sleep(10)
    easy_apply_filter = driver.find_element(By.CLASS_NAME, 'search-reusables__filter-binary-toggle')
    easy_apply_filter.click()


def get_job_urls(driver):
    job_elements = driver.find_elements(By.CLASS_NAME, "jobs-search-results__list-item")
    current_job_url = driver.current_url
    current_job_id_value = current_job_url.split("currentJobId=")[1].split("&")[0]
    job_applications_url = []
    for job_element in job_elements:
        job_id = job_element.get_attribute("data-occludable-job-id")
        changed_url = current_job_url.replace(f"currentJobId={current_job_id_value}", f"currentJobId={job_id}")
        job_applications_url.append(changed_url)
    return job_applications_url


predefined_answers = {
    "how many": "1",
    "experience": "1",
    "notice": "0",
    "sponsor": "No",
    "city": "Sangli",
    "AWS": "1",
    "do you": "Yes",
    "have you": "Yes",
    "Indian citizen": "Yes",
    "are you": "Yes",
    "expected ctc": "700000",
    "current ctc": "0",
    "can you": "Yes",
    "gender": "Male",
    "race": "Wish not to answer",
    "lgbtq": "Wish not to answer",
    "ethnicity": "Wish not to answer",
    "nationality": "Wish not to answer",
    "government": "I do not wish to self-identify",
    "legally": "Yes"
}


def get_answer(question, input_type="text"):
    question_lower = question.lower()
    for key, value in predefined_answers.items():
        if key in question_lower:
            return value
    if input_type == "text":
        if any(word in question_lower for word in ["experience", "years", "how many", "number of"]):
            return "0"
        return "0"
    elif input_type == "dropdown":
        return "No"
    else:
        return ""


def handle_form_fields(driver):
    wait = WebDriverWait(driver, 10)
    try:
        while True:
            form_fields = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".jobs-easy-apply-form-section__grouping")))
            for form in form_fields:
                question = form.text
                answer = get_answer(question)
                text_inputs = form.find_elements(By.CSS_SELECTOR, "input[type='text']")
                for text_input in text_inputs:
                    text_input.clear()
                    text_input.send_keys(answer)
                dropdowns = form.find_elements(By.CSS_SELECTOR, "select")
                for dropdown in dropdowns:
                    try:
                        select = Select(dropdown)
                        options = [option.text for option in select.options]
                        if answer in options:
                            select.select_by_visible_text(answer)
                        elif "Yes" in options and answer == "Yes":
                            select.select_by_visible_text("Yes")
                        elif "No" in options and answer == "No":
                            select.select_by_visible_text("No")
                        else:
                            select.select_by_index(2)
                    except Exception as e:
                        print(f"Error handling dropdown: {str(e)}")
                radio_buttons = form.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                if radio_buttons:
                    for radio in radio_buttons:
                        if radio.get_attribute("value").lower() == answer.lower():
                            driver.execute_script("arguments[0].click();", radio)
                            break
            clicked_next = click_next_button(driver)
            if clicked_next == "Submit":
                return
            time.sleep(2)
    except TimeoutException:
        print("Timeout waiting for form fields to load or next section.")
    except NoSuchElementException:
        print("Could not find form fields")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def click_next_button(driver):
    button_texts = ["Next", "Submit", "Review"]
    for text in button_texts:
        try:
            # Locate and click the button with matching text
            button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH,
                                            f"//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"))
            )
            button.click()
            print(f"Clicked the '{text}' button")

            # Special handling for the Submit button
            if text == "Submit":
                print("Final Submit button clicked. Waiting for confirmation.")
                time.sleep(5)

                # Wait for the success confirmation
                success_msg = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH,
                                                    "//div[contains(@class, 'artdeco-modal__content')]//h3[contains(text(), 'Your application was sent to')]"))
                )
                if success_msg:
                    print("Application submitted successfully!")
                else:
                    print("No confirmation message found. Verifying submission status...")
                    confirmation_dialog = driver.find_element(By.CLASS_NAME, "artdeco-modal__content")
                    if confirmation_dialog:
                        print("Confirmation dialog detected. Assuming the application was submitted.")
                    else:
                        print("Warning: Could not confirm if the application was submitted.")
                return "Submit"

            return text
        except Exception as e:
            print(f"Could not click '{text}' button: {str(e)}")

    print("Could not find Next, Submit, or Review button")
    return None


def apply_to_jobs(driver, job_applications_url):
    applied_jobs = []
    for job_url in job_applications_url:
        try:
            driver.get(job_url)
            print(f"Opened job page: {job_url}")
            time.sleep(3)
            try:
                job_card = driver.find_element(By.CSS_SELECTOR, "div[data-view-name='job-card']")
                job_role = job_card.find_element(By.CSS_SELECTOR,
                                                 ".full-width.artdeco-entity-lockup__title.ember-view").text
                company_name = job_card.find_element(By.CSS_SELECTOR, ".job-card-container__primary-description").text
                location = job_card.find_element(By.CSS_SELECTOR, ".job-card-container__metadata-item").text

                easy_apply_button = driver.find_element(By.CLASS_NAME, 'jobs-apply-button--top-card')
                print("Easy Apply button found, proceeding to apply...")
                continue_to_apply(driver)

                applied_job = {
                    "Company Name": company_name,
                    "Role": job_role,
                    "Location": location,
                    "URL": job_url
                }
                applied_jobs.append(applied_job)
                print(f"Applied to job: {job_url}")
                print("Application submitted successfully!")

                # Save job details to CSV after each successful application
                save_to_csv(applied_job)

            except NoSuchElementException:
                print("Easy Apply button not found, skipping to the next job.")
                continue
        except Exception as e:
            print(f"An error occurred with job URL {job_url}: {str(e)}")
            continue
    return applied_jobs


def continue_to_apply(driver):
    try:
        easy_apply_button = driver.find_element(By.CLASS_NAME, 'jobs-apply-button--top-card')
        easy_apply_button.click()
        click_next_button(driver)
        time.sleep(2)
        click_next_button(driver)
        time.sleep(2)
        handle_form_fields(driver)
        click_next_button(driver)
        time.sleep(2)
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def is_duplicate(applied_job, filename):
    if os.path.isfile(filename):
        with open(filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['Company Name'] == applied_job['Company Name'] and row['Role'] == applied_job['Role']:
                    return True
    return False


def save_to_csv(applied_job, filename="job_applications.csv"):
    if not is_duplicate(applied_job, filename):
        file_exists = os.path.isfile(filename)

        with open(filename, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=["Company Name", "Role", "Location", "URL"])
            if not file_exists:
                writer.writeheader()  # Write header only once when file is created
            writer.writerow(applied_job)  # Write the single job row

        print(f"Job application for {applied_job['Company Name']} - {applied_job['Role']} saved to {filename}")
    else:
        print(f"Duplicate found: {applied_job['Company Name']} - {applied_job['Role']}. Skipping saving.")


def run_linkedin_automation(cookies, search_keyword):
    driver = setup_driver()
    add_cookies(driver, cookies)
    search_jobs(driver, search_keyword)
    job_urls = get_job_urls(driver)
    applied_jobs = apply_to_jobs(driver, job_urls)
    # print(f"Applied jobs list: {applied_jobs}")
    # print("Saving applied jobs to CSV...")
    save_to_csv(applied_jobs)
    # print("CSV save process completed.")
    driver.quit()
    return "Job application process completed."