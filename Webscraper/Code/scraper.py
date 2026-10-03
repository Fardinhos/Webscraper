from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import csv
import time
import random
import re

def scrape_imdb_with_selenium(url, filename, target_movies=5):
    print(f"Opening browser for: {url}")
    print(f"Target number of movies to scrape: {target_movies}")
    
    driver = webdriver.Chrome() 
    
    try:
        driver.get(url)
        time.sleep(5) 
        
        # scroll to load all movies on the page
        while True:
            current_movies = driver.find_elements(By.CSS_SELECTOR, 'li.ipc-metadata-list-summary-item')
            loaded_count = len(current_movies)
            print(f"  -> Currently loaded: {loaded_count}/{target_movies} movies...")
            
            if loaded_count >= target_movies:
                break
                
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                load_more_btn = driver.find_element(By.CSS_SELECTOR, "button.ipc-see-more__button")
                driver.execute_script("arguments[0].click();", load_more_btn)
                time.sleep(3) 
                
                new_count = len(driver.find_elements(By.CSS_SELECTOR, 'li.ipc-metadata-list-summary-item'))
                if new_count == loaded_count:
                    break
            except Exception:
                break 
        
        print("Finished loading list. Extracting deep data...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        all_movies = soup.find_all('li', class_='ipc-metadata-list-summary-item')
        movies_to_process = all_movies[:target_movies]
        
        if not movies_to_process:
            print("No movies found.")
            return

        # write data to CSV file
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                'Title', 'Year', 'Duration', 'Rating', 'Votes', 
                'Metascore', 'Directors', 'Writers', 'Actors', 
                'Budget', 'Gross_Worldwide'
            ]) 
            
            for i, movie in enumerate(movies_to_process):
                print(f"  Scraping movie {i+1}/{target_movies}...")
                try:
                    # extract title, year, duration, rating from list
                    title_element = movie.find('h3', class_='ipc-title__text')
                    title = title_element.text.split('. ', 1)[-1] if title_element else "N/A"
                    
                    metadata_spans = movie.find_all('span', class_='dli-title-metadata-item')
                    year = metadata_spans[0].text if len(metadata_spans) > 0 else "N/A"
                    duration = metadata_spans[1].text if len(metadata_spans) > 1 else "N/A"
                    
                    # Split Rating and Votes
                    rating_element = movie.find('span', class_='ipc-rating-star')
                    if rating_element:
                        parts = rating_element.text.strip().split('(')
                        rating = parts[0].strip()
                        votes = parts[1].replace(')', '').strip() if len(parts) > 1 else "N/A"
                    else:
                        rating, votes = "N/A", "N/A"
                    
                    # click on each movie to get detailed info
                    link_element = movie.find('a', class_='ipc-title-link-wrapper')
                    movie_url = "https://www.imdb.com" + link_element['href']
                    
                    driver.execute_script(f"window.open('{movie_url}', '_blank');")
                    driver.switch_to.window(driver.window_handles[1])
                    
                    try:
                        time.sleep(1.5) # Let the movie page load
                        movie_soup = BeautifulSoup(driver.page_source, 'html.parser')
                        
                        # get list of actors
                        try:
                            cast_section = movie_soup.find(lambda tag: tag.name in ['a', 'span'] and tag.text == 'Stars')
                            if cast_section:
                                actors_list = cast_section.find_parent('li').find_all('a', class_='ipc-metadata-list-item__list-content-item')
                                actors = ", ".join([a.text for a in actors_list])
                            else: actors = "N/A"
                        except: actors = "N/A"

                        # get directors
                        try:
                            dir_section = movie_soup.find(lambda tag: tag.name in ['a', 'span'] and 'Director' in tag.text)
                            if dir_section:
                                dir_list = dir_section.find_parent('li').find_all('a', class_='ipc-metadata-list-item__list-content-item')
                                directors = ", ".join([d.text for d in dir_list])
                            else: directors = "N/A"
                        except: directors = "N/A"

                        # get writers
                        try:
                            writer_section = movie_soup.find(lambda tag: tag.name in ['a', 'span'] and tag.text in ['Writer', 'Writers'])
                            if writer_section:
                                writer_list = writer_section.find_parent('li').find_all('a', class_='ipc-metadata-list-item__list-content-item')
                                writers = ", ".join([w.text for w in writer_list])
                            else: writers = "N/A"
                        except: writers = "N/A"

                        # get budget
                        try:
                            budget_label = movie_soup.find(string=re.compile('Budget', re.I))
                            if budget_label:
                                budget = budget_label.find_parent('li').find('span', class_='ipc-metadata-list-item__list-content-item').text
                            else: budget = "N/A"
                        except: budget = "N/A"

                        # get worldwide gross
                        try:
                            gross_label = movie_soup.find(string=re.compile('Gross worldwide', re.I))
                            if gross_label:
                                gross = gross_label.find_parent('li').find('span', class_='ipc-metadata-list-item__list-content-item').text
                            else: gross = "N/A"
                        except: gross = "N/A"

                        # get metascore
                        try:
                            metascore_span = movie_soup.find('span', class_='metacritic-score-box')
                            metascore = metascore_span.text.strip() if metascore_span else "N/A"
                        except: metascore = "N/A"

                    except Exception as e:
                        # If page fails to load, fill with N/A
                        actors, directors, writers, budget, gross, metascore = "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"
                        
                    # close tab and go back to main page
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    
                    # save to CSV
                    writer.writerow([title, year, duration, rating, votes, metascore, directors, writers, actors, budget, gross])
                
                except Exception as e:
                    continue

        print(f"Successfully saved {len(movies_to_process)} movies to {filename}\n")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    resources = [
        {"url": "https://www.imdb.com/search/title/?title_type=feature&genres=sci-fi&sort=num_votes,desc", "filename": "top_scifi.csv"},
        {"url": "https://www.imdb.com/search/title/?title_type=feature&genres=action&sort=num_votes,desc", "filename": "top_action.csv"},
        {"url": "https://www.imdb.com/search/title/?title_type=feature&genres=horror&sort=num_votes,desc", "filename": "top_horror.csv"}
    ]

    # number of movies to scrape
    MOVIES_TO_SCRAPE = 500

    for resource in resources:
        scrape_imdb_with_selenium(resource['url'], resource['filename'], target_movies=MOVIES_TO_SCRAPE)
        
        sleep_time = random.uniform(3, 6)
        print(f"Sleeping for {sleep_time:.2f} seconds before the next category...\n")
        time.sleep(sleep_time)
        
    print("Done. All CSVs saved.")